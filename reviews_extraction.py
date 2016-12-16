#load webdriver function from selenium
from selenium import webdriver
from time import sleep
from bs4 import BeautifulSoup, Comment
import pandas as pd


#Setting up Chrome webdriver Options
chrome_options = webdriver.ChromeOptions()

#setting  up local path of chrome binary file 
chrome_options.binary_location = "C:\\Users\\SA31\\Downloads\\dt\\Win_337026_chrome-win32\\chrome-win32\\chrome.exe"

#creating Chrome webdriver instance with the set chrome_options
driver = webdriver.Chrome(chrome_options=chrome_options)
link = "https://play.google.com/store/apps/details?id=uk.co.o2.android.myo2&hl=en_GB" 
driver.get(link)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

driver.find_element_by_xpath('//*[@id="body-content"]/div/div/div[1]/div[2]/div[2]/div[1]/div[4]/button[2]/div[2]').click()

sleep(1)

reviews_df = []
for i in range(1,6):
    driver.find_element_by_xpath('//*[@id="body-content"]/div/div/div[1]/div[2]/div[2]/div[1]/div[4]/button[2]/div[2]/div/div').click()
    sleep(1)
    for elem in driver.find_elements_by_class_name('review-text'):
        content = elem.get_attribute('innerHTML')
        soup = BeautifulSoup(content, "html.parser")
        print(soup.get_text())
        temp = pd.DataFrame({'Review Text':soup.get_text()},index=[0])
        print('-'*10)
        reviews_df.append(temp)
reviews_df1 = pd.concat(reviews_df,ignore_index=True)

reviews_df1.to_csv('reviews_list.csv', encoding='utf-8')
 
driver.close()
    
