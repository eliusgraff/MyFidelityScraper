# Python-Scraper

  This is a personal project to keep me entertained until I find a full-time engineering job. The hope is to keep track of my various Fidelity accounts and compare 
 their performances against one another over various time intervals. 
 Fidelity does a poor job of giving great feedback on positions as they
 compare to other positions in your potfolio and does not account for
 dividends.
 
 We will have to use a class to scrape a Fidelity account for investment 
 data since there is no web API. Fidelity provides a downloadable .CSV 
 file containing account data so once that file is downloaded, it will 
 be processed and stored elsewhere (maybe Google Drive?) so that the
 collected data is persistent and therefore code runs faster and data
 is more meaningful. This code will be written with hope that it is 
 collecting data daily unless told to collect more data by user.
 
 All data collected will be stored so that the user can access it and
 view their performance compared to broader market. As time goes on, it
 would be nice to be able to write algorithms and get stock reccomendations
 based on what I (or any user) values.
