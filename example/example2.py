from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import undetected as uc


def main():
    driver = uc.Chrome()
    driver.get("https://google.com")

    sleep(5)  # Pode ser substituído por um WebDriverWait

    driver.execute_script("""document.querySelector("#W0wltc").click()""")

    inp_search = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "q"))
    )

    inp_search.send_keys("site:stackoverflow.com undetected chromedriver\n")

    sleep(5)
    driver.quit()


main()
