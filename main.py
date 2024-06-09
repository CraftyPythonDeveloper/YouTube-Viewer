import json
import os.path
import signal
import threading
import time
import zipfile
from queue import Queue
from random import choice

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def load_proxies(file_name):
    with open(file_name, 'r') as f:
        return list(set([proxy.strip() for proxy in f.readlines() if proxy]))


def set_referer(url, method, driver, referrers):
    referer = choice(referrers)
    if referer:
        if method == 2 and 't.co/' in referer:
            driver.get(url)
        else:
            if 'yahoo.com' in referer:
                driver.get('https://duckduckgo.com/')
                driver.execute_script(
                    "window.history.pushState('page2', 'Title', arguments[0]);", referer)
            else:
                driver.get(referer)
            # if datetime.now().date() > datetime(year=2023, month=7, day=1).date():
            #     return driver.get('https://google.com')
            driver.execute_script("window.location.href = '{}';".format(url))
    else:
        driver.get(url)


def create_driver_with_proxy(prox=None):
    try:
        login_details, host_details = prox.strip("http://").split("@")
        username, password = login_details.split(":")
        ip, port = host_details.split(":")
    except ValueError:
        schema, username, password, ip, port = [None]*5

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')

    PROXY_HOST = ip
    PROXY_PORT = port
    PROXY_USER = username
    PROXY_PASS = password

    if PROXY_HOST and PROXY_USER and PROXY_PASS and PROXY_PORT:
        manifest_json = """
                 {
                     "version": "1.0.0",
                     "manifest_version": 2,
                     "name": "Chrome Proxy",
                     "permissions": [
                         "proxy",
                         "tabs",
                         "unlimitedStorage",
                         "storage",
                         "<all_urls>",
                         "webRequest",
                         "webRequestBlocking"
                     ],
                     "background": {
                         "scripts": ["background.js"]
                     },
                     "minimum_chrome_version":"22.0.0"
                 }
                 """
        background_js = """
             var config = {
                     mode: "fixed_servers",
                     rules: {
                     singleProxy: {
                         scheme: "http",
                         host: "%s",
                         port: parseInt(%s)
                     },
                     bypassList: ["localhost"]
                     }
                 };
             chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
             function callbackFn(details) {
                 return {
                     authCredentials: {
                         username: "%s",
                         password: "%s"
                     }
                 };
             }
             chrome.webRequest.onAuthRequired.addListener(
                         callbackFn,
                         {urls: ["<all_urls>"]},
                         ['blocking']
             );
             """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        pluginfile = os.path.join(os.path.join(os.getcwd(), 'proxies'), f'{PROXY_PORT}-proxy_auth_plugin.zip')
        try:
            if os.path.exists(pluginfile):
                chrome_options.add_extension(pluginfile)
            else:
                with zipfile.ZipFile(pluginfile, 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr("background.js", background_js)
                chrome_options.add_extension(pluginfile)
        except:
            pass
        pluginfile =os.path.join(os.path.join(os.getcwd(), 'proxies'))
        manifes_path = os.path.join(pluginfile, 'manifest.json')
        backgrond_path = os.path.join(pluginfile, 'background.js')
        with open(manifes_path, 'w') as f:
            json_data = json.loads(manifest_json)
            json.dump(json_data, f)
        with open(backgrond_path, 'w') as f:
            f.write(background_js)
        chrome_options.add_argument('--disable-popup-blocking')

        chrome_options.add_argument(f'--load-extension={pluginfile}')

    chrome_options.add_argument('--disable-popup-blocking')
    # services = Service(ChromeDriverManager().install())

    return webdriver.Chrome(options=chrome_options)


def open_and_refresh_youtube_video(url, proxy_queue, referrers):
    # proxy = proxy_queue.get()  # Get a unique proxy from the queue

    proxy = proxy_queue.get() if proxy_queue is not None else None # Get a unique proxy from the queue
    driver = None
    try:
        driver = create_driver_with_proxy(proxy)
        set_referer(url, 1, driver, referrers)
    except:
        if proxy:
            proxy_queue.put(proxy)
        driver.quit()
        return None
    try:
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH,
                                                                   '//button[@aria-label="Accept the use of cookies and other data for the purposes described"]'))).click()
    except:
        pass

    try:
        WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.TAG_NAME, 'video')))
    except:
        pass

    while True:
        try:
            waitForAd = '''if (document.querySelector("div.ad-showing"))
                                      return true
                                  return false
                              '''
            is_add = driver.execute_script(waitForAd)
            try:
                if driver.execute_script(
                        'return document.getElementsByClassName("video-stream html5-main-video")[0].paused'):
                    driver.execute_script('document.getElementsByClassName("video-stream html5-main-video")[0].play();')
            except:
                pass
            try:
                check_loop = driver.execute_script(
                    'return document.getElementsByClassName("video-stream html5-main-video")[0].loop;')

                if not check_loop and not is_add:

                    playInLoop = '''const video = document.getElementsByClassName("video-stream html5-main-video")[0];
                                                 video.loop = true
                                          '''
                    driver.execute_script(playInLoop)
                    try:
                        quality = driver.execute_script(
                            'return document.getElementsByClassName("ytp-settings-button")[0]')
                        driver.execute_script('arguments[0].click()', quality)
                        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                    '//div[@class="ytp-panel"]//div[text()="Quality"]/parent::div[@class="ytp-menuitem"]'))).click()
                        quatliy_144 = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                  '//div[contains(@class,"ytp-quality-menu")]/div[@class="ytp-panel-menu"]//span[text()="144p"]/ancestor::div[@role="menuitemradio"]')))
                        quatliy_144.click()
                    except:
                        pass
            except:
                pass

            try:
                is_video = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'video')))
                if is_video:
                    continue
            except:
                pass


        except:
            driver.quit()
            break  # Break the inner loop and start a new thread with a new proxy

    # Add the used proxy back to the queue for reuse
    if proxy:
        proxy_queue.put(proxy)


def signal_handler(signal, frame):
    print("Exiting...")
    os._exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    tabs = int(input("Number of Tabs: "))
    delay = int(input("Delay In Secs: "))

    proxies = load_proxies('Proxy.txt')
    video_urls = []
    for i in range(int(tabs)):
        url = input(f"Enter the URL for video: ")
        if url:
            video_urls.append(url)

    refer = ['https://www.google.com/', 'https://www.bing.com/']
    proxy_queue = Queue()  # Create a shared queue for proxies
    if len(proxies)>0:
        for proxy in proxies:
            proxy_queue.put(proxy)  # Add each proxy to the queue
    else:
        proxy_queue = None
    threads = []
    for url in video_urls:
        thread = threading.Thread(target=open_and_refresh_youtube_video, args=(url, proxy_queue, refer))
        thread.start()
        threads.append(thread)
        time.sleep(delay)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Stopping threads...")
        for thread in threads:
            thread.join()


if __name__ == "__main__":
    main()
