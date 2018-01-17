# -*- coding: utf-8 -*-
import scrapy
from selenium import webdriver
from time import sleep
from scrapy.selector import Selector

class ProductsSpider(scrapy.Spider):
    name = 'products'

    def start_requests(self):
        url = 'https://ecomhunt.com/login'
        self.driver = webdriver.Chrome()
        sleep(1)
        self.driver.get(url)
        sleep(1)
        self.login()
        sel = Selector(text=self.driver.page_source)
        all_links = sel.xpath("//a[contains(text(),'SHOW ME THE MONEY')]/@href").extract()
        cookies_list = self.driver.get_cookies()
        self.cookies_dict = {}
        for cookie in cookies_list:
            self.cookies_dict[cookie['name']] = cookie['value']
        for link in all_links:
            yield scrapy.Request(link,cookies=self.cookies_dict,callback=self.parse)

        next_page_url = sel.xpath("//ul[@class='pagination']/li/a[@rel='next']/@href").extract_first()

        while next_page_url:
            self.driver.get(next_page_url)
            sleep(2)
            sel = Selector(text=self.driver.page_source)
            all_links = sel.xpath("//a[contains(text(),'SHOW ME THE MONEY')]/@href").extract()
            cookies_list = self.driver.get_cookies()
            self.cookies_dict = {}
            for cookie in cookies_list:
                self.cookies_dict[cookie['name']] = cookie['value']
            for link in all_links:
                yield scrapy.Request(link,cookies=self.cookies_dict,callback=self.parse)

            next_page_url = sel.xpath("//ul[@class='pagination']/li/a[@rel='next']/@href").extract_first()


    def login(self):
        username = self.driver.find_element_by_xpath("//input[@id='email']")
        username.send_keys('your email id')
        password = self.driver.find_element_by_xpath("//input[@id='password']")
        password.send_keys('your password')
        password.submit()
        sleep(3)

    def parse(self,response):
        title = response.xpath("//div[contains(@class,'main-info')]/h3/text()").extract_first()
        shop_url = response.xpath("//div[@id='info-links']/div[@class='links-container']/p/a[contains(text(),'Store Selling This Item')]/@href").extract_first()
        fb_ad_url = response.xpath("//div[@id='info-links']/div[@class='links-container']/p/a[contains(text(),'Facebook Ad')]/@href").extract_first()

        yield scrapy.Request(fb_ad_url,callback=self.parse_fb,meta={
            'title':title,
            'shop_url':shop_url,
            'fb_ad_url':fb_ad_url
        })

    def parse_fb(self,response):
        title = response.meta['title']
        fb_ad_url = response.url
        shop_url = response.meta['shop_url']

        yield scrapy.Request(shop_url,callback=self.parse_shop,meta={
            'title':title,
            'shop_url':shop_url,
            'fb_ad_url':fb_ad_url
        })

    def parse_shop(self,response):
        title = response.meta['title']
        fb_ad_url = response.meta['fb_ad_url']
        shop_url = response.url
        yield {
            'title':title,
            'shop_url':shop_url,
            'fb_ad_url':fb_ad_url
        }

    def close(self):
        self.driver.quit()
