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
#driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
Ptitle = driver.find_element_by_class_name('id-app-title').text.replace(' ','')
print(Ptitle)
#driver.find_element_by_xpath('//*[@id="body-content"]/div/div/div[1]/div[2]/div[2]/div[1]/div[4]/button[2]/div[2]').click()

sleep(1)
driver.find_element_by_xpath('//*[@id="body-content"]/div/div/div[1]/div[2]/div[2]/div[1]/div[4]/button[2]/div[2]/div/div').click()
#select_newest.select_by_visible_text('Newest')                       
#driver.find_element_by_xpath('//*[@id="body-content"]/div/div/div[1]/div[2]/div[2]/div[1]/div[4]/button[2]/div[2]/div/div').click()
sleep(2)
#driver.find_element_by_css_selector('.review-filter.id-review-sort-filter.dropdown-menu-container').click()
driver.find_element_by_css_selector('.displayed-child').click()
#driver.find_element_by_xpath("//button[@data-dropdown-value='1']").click()
driver.execute_script("document.querySelectorAll('button.dropdown-child')[0].click()")
reviews_df = []
for i in range(1,5):
    try:
        for elem in driver.find_elements_by_class_name('single-review'):
            print(str(i))
            content = elem.get_attribute('outerHTML')
            soup = BeautifulSoup(content, "html.parser")
            #print(soup.prettify())
            date = soup.find('span',class_='review-date').get_text()
            rating = soup.find('div',class_='tiny-star')['aria-label'][6:7]
            title = soup.find('span',class_='review-title').get_text()
            txt = soup.find('div',class_='review-body').get_text().replace('Full Review','')[len(title)+1:]
            print(soup.get_text())
            temp = pd.DataFrame({'Date':date,'Rating':rating,'Review Title':title,'Review Text':txt},index=[0])
            print('-'*10)
            reviews_df.append(temp)
            #print(elem)
    except:
        print('s')
    driver.find_element_by_xpath('//*[@id="body-content"]/div/div/div[1]/div[2]/div[2]/div[1]/div[4]/button[2]/div[2]/div/div').click()
reviews_df = pd.concat(reviews_df,ignore_index=True)

reviews_df.to_csv(Ptitle+'_reviews_list.csv', encoding='utf-8')
 
#driver.close()
    
