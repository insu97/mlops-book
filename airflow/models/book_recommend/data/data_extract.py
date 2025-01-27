# Define the functions
import requests
import pandas as pd
import json


def search_books(ttbkey, query, df, queryType="Keyword", start=1, MaxResults=50, sort="Accuracy"):
    url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "TTBKey": ttbkey,
        "Query": query,
        "QueryType": queryType,
        "start": start,
        "MaxResults": MaxResults,
        "Sort": sort,
        "Cover": "None",
        "CategoryId": "0",
        "output": "js",
        "SearchTarget": "Book",
        "Version": "20131101",
        "outofStockfilter": 1,
        "RecentPublishFilter": 0,
    }

    response = requests.get(url, params=params)
    data = json.loads(response.text)

    if "item" in data:
        items = []
        for item in data["item"]:
            book_info = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "author": item.get("author", ""),
                "pubDate": item.get("pubDate", ""),
                "description": item.get("description", ""),
                "isbn": item.get("isbn", ""),
                "isbn13": item.get("isbn13", ""),
                "itemId": item.get("itemId", ""),
                "priceSales": item.get("priceSales", ""),
                "priceStandard": item.get("priceStandard", ""),
                "categoryId": item.get("categoryId", ""),
                "categoryName": item.get("categoryName", ""),
                "publisher": item.get("publisher", ""),
                "customerReviewRank": item.get("customerReviewRank", ""),
            }
            items.append(book_info)

        df = pd.concat([df, pd.DataFrame(items)], ignore_index=True)

    return df


def collect_books(ttbkey, query, max_books=500):
    df = pd.DataFrame(columns=[
        "title", "link", "author", "pubDate", "description", "isbn", "isbn13",
        "itemId", "priceSales", "priceStandard", "categoryId", "categoryName",
        "publisher", "customerReviewRank",
    ])

    start = 1
    max_results_per_call = 50

    while len(df) < max_books:
        df = search_books(ttbkey, query, df, start=start, MaxResults=max_results_per_call)
        start += max_results_per_call
        if len(df) == len(df.drop_duplicates()):
            break

    df = df.head(max_books)
    return df


def search_and_collect_books(**kwargs):
    ttbkey = kwargs['params']['ttbkey']
    query = kwargs['params']['query']
    collected_books = collect_books(ttbkey, query)
    kwargs['ti'].xcom_push(key='collected_books', value=collected_books.to_json())
