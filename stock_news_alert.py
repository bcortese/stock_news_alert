#!/usr/bin/env python
# coding: utf-8



import robin_stocks as r
import pandas as pd
import csv
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Import the email modules we'll need
import smtplib
from email.mime.text import MIMEText



#connect to RobinHood api
def login(path):
  with open(path, newline='') as f:
      reader = csv.reader(f)
      row1 = next(reader)  # gets the first line
      r.login(row1[0],row1[1])

def getGoogleSheetsInfo(sheetName):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\login_files\\stockwatchlist_creds.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheetName).sheet1
    data = sheet.col_values(1)  # Get a list of all records
    return data
    
def main():
    #read credential files.
    login("C://login_files//robinHood_Login.csv")
    
    #watchlist items...because the watchlist api doesnt function well.
    mylist = getGoogleSheetsInfo("StockWatchlist")
    
    
    keywords = getGoogleSheetsInfo("stock_popularKeywords")
    
    my_stocks = r.build_holdings()
    for key,value in my_stocks.items():
        mylist.append(key)
    TODAY_CHECK = datetime.now()
    weekOldArticle = TODAY_CHECK - timedelta(7) 
    weekOldArticle = weekOldArticle.strftime('%m/%d/%y')
    
    
    # SMTP() is used with normal, unencrypted (non-SSL) email.
    # To send email via an SSL connection, use SMTP_SSL().
    server = smtplib.SMTP('smtp.gmail.com', 587)
    
    # Specifying an empty server.connect() statement defaults to ('localhost', 25).
    # Therefore, we specify which mail server we wish to connect to.
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    
    # Optional login for the receiving mail_server.
    server.login ('user', 'pass')
    
    messageBody = ""
    for stock in mylist: 
    
        data = r.stocks.get_news(stock)
    
        df = pd.DataFrame(data, columns=['updated_at', 'title', 'url', 'preview_text'])
    
    
        #updating date format to compare with a week old date. 
        #Setting flag up to only show week old articles.
        df['updated_at'] = pd.to_datetime(df.updated_at)
        df['articleDate'] = df['updated_at'].dt.strftime('%m/%d/%Y')
        isWithinOneWeek = df['articleDate'] >= weekOldArticle
        updatedData = df[isWithinOneWeek]
        #filtering out articles not containing the popular key words
        latestArticles = pd.DataFrame(updatedData)
        popularArticleFilter = latestArticles.title.apply(lambda x: any(item for item in keywords if item.lower() in x.lower()))
        recentPopularArticles = latestArticles[popularArticleFilter]
        
        for count, badDate, title, url, preview, goodDate in recentPopularArticles.itertuples():
            
            messageBody += goodDate + " STOCK: " + stock + '\n' + "Article: " + title + '\n' + "URL: " + url + '\n'
            messageBody += '\n' + "SUMMARY: " + preview + '\n' + '\n'

    msg = MIMEText(messageBody)
    
    
    
    # Create our message. 
    msg['Subject'] = 'Watched/Owned Stocks News'
    
    # path bounced emails.
    try:
        server.sendmail('brandoncortese04@gmail.com', ['brandoncortese04@gmail.com'], msg.as_string())
    finally:
        server.quit()
    
    recentPopularArticles.to_csv('D:/programming/envs/Fun_place/Scripts/test.csv')
    
if __name__== "__main__":
   main()