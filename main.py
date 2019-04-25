import logging
from pyclick.humancurve import HumanCurve
from sys import path
from time import sleep
from json import dumps
from random import uniform, randint
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

logging.basicConfig(format='Line: %(lineno)d, %(levelname)s:%(message)s', level=logging.WARNING)


def human_send_keys(driver, element, input_str, delay_range=[0.1, 0.7]):
    """ Mimics a human while using send_keys"""
    if not isinstance(input_str, str):
        logging.error('Non-string input to send keys!')
        return 1
    else:

        input_str = list(input_str)
        for char in input_str:
            sleep(uniform(delay_range[0], delay_range[1]))
            element.send_keys(char)
        return 0


def human_mouse_move(driver, element):
    x_cord = element.location['x']
    y_cord = element.location['y']

    # Generate human-like bezier curve, starting at either x or y 0.
    if randint(1,2) == 1:
        human_curve = HumanCurve([0, randint(0, 600)], [x_cord, y_cord])
    else:
        human_curve = HumanCurve([randint(0, 600), 0], [x_cord, y_cord])

    action = ActionChains(chrome_window)

    # Move to each point in the list.
    for point in human_curve.points:
        action.move_by_offset(point[0], point[1])
        action.perform()


def human_click(driver, element):
    pass


def send_devtool_cmd(driver, cmd, params={}):
    resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
    url = driver.command_executor._url + resource
    body = dumps({'cmd': cmd, 'params': params})
    response = driver.command_executor._request('POST', url, body)
    if response['status']:
        raise Exception(response.get('value'))

    return response.get('value')


def preload_jscript(driver, script):
  send_devtool_cmd(driver, "Page.addScriptToEvaluateOnNewDocument", {"source": script})


def open_chrome(useragent=None, *kwargs):
    if useragent is None:
        useragent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                    'Chrome/73.0.3683.75 Safari/537.36'

    options = Options()
    options.add_argument(f'user-agent={useragent}')
    options.add_argument("disable-infobars")

    for arg in kwargs:
        options.add_argument(arg)

    WebDriver.add_script = preload_jscript

    # Launch chrome, variable global so window stays open.
    global chrome_window
    chrome_window = webdriver.Chrome(executable_path=path[0]+'/chromedriver', chrome_options=options)

    webgl_ = ['NVIDIA Corporation', 'Intel Open Source Technology Center' ]
    # Preload script to avoid detection, mostly taken from https://intoli.com/blog/making-chrome-headless-undetectable/
    # Line 126 to update broken image size if chrome updates this.
    chrome_window.add_script("""
// overwrite the `languages` property to use a custom getter
Object.defineProperty(navigator, 'languages', {
    get: function() {
        return ['en-US', 'en'];
    },
});

// overwrite the `plugins` property to use a custom getter
Object.defineProperty(navigator, 'plugins', {
  get: function() {
    // this just needs to have `length > 0`, but we could mock the plugins too
    return [1, 2, 3, 4, 5];
  },
});

const getParameter = WebGLRenderingContext.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
  // UNMASKED_VENDOR_WEBGL
  if (parameter === 37445) {
    return 'Intel Open Source Technology Center';
  }
  // UNMASKED_RENDERER_WEBGL
  if (parameter === 37446) {
    return 'Mesa DRI Intel(R) Ivybridge Mobile ';
  }

  return getParameter(parameter);
};
    
['height', 'width'].forEach(property => {
  // store the existing descriptor
  const imageDescriptor = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, property);

  // redefine the property with a patched descriptor
  Object.defineProperty(HTMLImageElement.prototype, property, {
    ...imageDescriptor,
    get: function() {
      // return an arbitrary non-zero dimension if the image failed to load
      if (this.complete && this.naturalHeight == 0) {
        return 16;
      }
      // otherwise, return the actual dimension
      return imageDescriptor.get.apply(this);
    },
  });
});
    
if (window.self === window.top) { // if main document
    console.log('add script');
}
  """)

    return 0


def login_discord(email, password, speed=3):

    open_chrome()

    # Open Discord.
    chrome_window.get("https://discordapp.com/channels/@me")

    # Find our inputs and buttons via xpath.
    email_input = chrome_window.find_element_by_xpath('//*[@id="app-mount"]/div[1]/div/div[2]/div/form/'
                                                      'div/div[3]/div[1]/div/input')
    password_input = chrome_window.find_element_by_xpath('//*[@id="app-mount"]/div[1]/div/div[2]/div/form/'
                                                         'div/div[3]/div[2]/div/input')
    login_button = chrome_window.find_element_by_xpath('//*[@id="app-mount"]/div[1]/div/div[2]/div/form/'
                                                       'div/div[3]/button[2]')

    # Random int decides behaviour pattern.
    percentage = randint(0, 100)

    # Determine typing speed
    if speed > 5:
        logging.warning("Action speed set above 5, may cause bot-detection and reliability issues.")

    min_delay = 0.25 / speed
    max_delay = 2 / speed

    # Random sleeps between inputing username and password
    sleep(uniform(min_delay, max_delay))
    human_send_keys(chrome_window, email_input, email)
    sleep(uniform(min_delay, max_delay))
    email_input.send_keys(u'\ue004')
    sleep(uniform(min_delay, max_delay))
    human_send_keys(chrome_window, password_input, password)
    sleep(uniform(min_delay, max_delay))

    if percentage >= 35:
        email_input.send_keys(u'\ue007')
    else:
        human_mouse_move(chrome_window, login_button)
        login_button.click()

    # Blocks Discord analytics using DevTool API.
    send_devtool_cmd(chrome_window, "Network.setBlockedURLs", {'urls': ["https://discordapp.com/api/v6/science"]})
    send_devtool_cmd(chrome_window, "Network.enable")


def scrape_discord_servers(driver):
    # Blocks Discord analytics using DevTool API.
    send_devtool_cmd(chrome_window, "Network.setBlockedURLs", {'urls': ["https://discordapp.com/api/v6/science"]})
    send_devtool_cmd(chrome_window, "Network.enable")
    pass


def scrape_startpage(search_terms, proxies=None):
    if proxies is None:
        pass

    for term in search_terms:
        pass


login_discord("","")