import requests
import json
import pandas as pd
import os.path
import nltk
import numpy as np


fiction = ['Date', 'Romance', 'Fantasy', 'Action Adventure', 'Science Fiction', 'Suspense/Thriller', 'Young Adult', 'Horror', 'Mystery', 'Historical Fiction', 'Literary Fiction', 'Graphic Novel', 'Dystopian', 'Other']
nonfiction = ['Date', 'History', 'Biography', 'Memoir/Autobiography', 'Memoir', 'Travel', 'Academic', 'Philosophy', 'Journal', 'Humor', 'Health and Fitness', 'Business', 'Law', 'Education', 'Politics', 'Social Science', 'Food and Drink', 'Science', 'Technology',  'Other']

class GoogleBook():
    api_key = ''
    properties = ['title', 'inauthor', 'isbn', 'inpublisher']
    def __init__(self, title, inauthor = None, isbn = None, inpublisher = None):
        self.title = title
        self.inauthor = inauthor
        self.isbn = isbn
        self.inpublisher = inpublisher
        self.url = 'https://www.googleapis.com/books/v1/volumes?q='
    def get_data(self):
        ## grab genre of book using queries (title, author, isbn, publisher...)
        ## return dictionary of each book result (dict.keys() = number of books returned)
        self.url += self.title
        if self.inauthor != None:
            self.url += '+inauthor:'
            self.url += self.inauthor
        if self.isbn != None:
            self.url += '+isbn:'
            self.url += str(self.isbn)
        if self.inpublisher != None:
            self.url += '+inpublisher:'
            self.url += str(self.inpublisher)
        print('final self.url: ' + str(self.url))
        r = requests.get(self.url)
        text = json.loads(r.text)
        oDict = {}
        for num, item in enumerate(text['items']):
            oDict[str(num)] = item
        return oDict

def filter_text(book):
    oDict = book.get_data() # keys: 'kind', 'id', 'etag', 'selfLink', 'volumeInfo', 'saleInfo', 'accessInfo', 'searchInfo'
    # selfLink - Google Books link     
    # volumeInfo - pageCount, averageRating, ratingsCount, language, categories
    # saleInfo - country, saleability, isEbook
    # accessInfo - country, pnonfictiondf
    # searchInfo - textSnippet
    key = verify_book(oDict)
    if key != None:
        title = oDict[key]['volumeInfo']['title']
        try:
            genre = oDict[key]['volumeInfo']['categories']
        except KeyError:
            return None, None, None
        try:
            subtitle = oDict[key]['volumeInfo']['subtitle']
            return genre, title, subtitle
        except KeyError:
            return genre, title, None

def verify_book(data):
    # confirm correct book by the user
    properties = ['title', 'subtitle', 'authors', 'publisher']
    for key in data.keys(): # each key represents each book
        for property in properties:
            try:
                d = data[key]['volumeInfo'][property]
                print(str(property) + ': ' + str(", ".join(d) if type(d) == list else d))
                print('')
            except KeyError:
                pass
        yn = int(input('Is this book correct? (0-yes, 1-no)'))
        if yn == 0:
            return key
        elif yn == 1:
            continue
        else:
            print('try searching with more queries or different title')
            return None

def setup_csv():
    ## setup a csv file to save book data 
    if os.path.isfile('fiction.csv') == False:
        fictiondf = pd.DataFrame(columns = fiction)
        fictiondf.to_csv('fiction.csv')
    if os.path.isfile('nonfiction.csv') == False:
        nonfictiondf = pd.DataFrame(columns = nonfiction)
        nonfictiondf.to_csv('nonfiction.csv')

def genre_check(current, past):
    # return similarity score 
    if type(current) == list:
        current = " ".join(current)
    similar = nltk.edit_distance(current.lower(), past.lower())
    return similar

def input_data(book):
    fictiondf = pd.read_csv('fiction.csv', index_col = 0)
    nonfictiondf = pd.read_csv('nonfiction.csv', index_col = 0)
    genre, title, subtitle = filter_text(book)
    if genre == None:
        print('No genre available for this book, try again with a different book')
        return None
    if subtitle != None: # some books dont have subtitles, so dont add subtitle name if none available
        full_title = str(title) + ' ' + str(subtitle)
    else:
        full_title = str(title)
    if type(full_title) == list:
        full_title = "".join(full_title)
    sort_genre(fictiondf, nonfictiondf, full_title, genre)

def sort_genre(f, nf, t, ge):
    l, i, g = most_similar(ge) #score, index, genre
    if g == 'Fiction':
        genre = fiction[i]
        "".join(genre) if type(genre) == list else genre
        missing_index = f[f[genre].isnull()].index.tolist()
        try:
            if f[genre].str.contains(t).any() == True:
                print('Already read book')
                return None
        except AttributeError:
            pass
        if len(missing_index) > 0:
            print(missing_index[0])
            f[genre][missing_index[0]] = t
        else:
            tempdf = {genre: t}
            f = f.append(tempdf, ignore_index = True)
        f.to_csv('fiction.csv')
    elif g == 'Nonfiction':
        genre = nonfiction[i]
        "".join(genre) if type(genre) == list else genre
        missing_index = nf[nf[genre].isnull()].index.tolist()
        try:
            if nf[genre].str.contains(t).any() == True:
                print('Already read book')
                return None
        except AttributeError:
            pass
        if len(missing_index) > 0:
            print(missing_index[0])
            nf[genre][missing_index[0]] = t
        else:
            tempdf = {genre: t}
            nf = nf.append(tempdf, ignore_index = True)
        nf.to_csv('nonfiction.csv')
    else: # 'Other' Branch | will add the book to both csv files under 'other' column
        try:
            if nf['Other'].str.contains(t).any() == True:
                print('Already read book')
                return None
        except AttributeError:
            pass
        missing_index1 = f[f['Other'].isnull()].index.tolist()
        missing_index2 = nf[nf['Other'].isnull()].index.tolist()
        if len(missing_index1) > 0:
            f['Other'][missing_index1[0]] = t
        else:
            tempdf = {'Other': t}
            f = f.append(tempdf, ignore_index = True)
        if len(missing_index2) > 0:
            nf['Other'][missing_index2[0]] = t
        else:
            tempdf = {'Other': t}
            nf = nf.append(tempdf, ignore_index = True)

def most_similar(genre):
    print(genre)
    if type(genre) == list:
        genre = "".join(genre)
    for num, g in enumerate(fiction):
        if num == 0:
            pass # skip 'Date' column 
        elif num == 1:
            low1 = genre_check(genre, g)
            index1 = num
        elif genre_check(genre, g) < low1:
            low1 = genre_check(genre, g)
            index1 = num     
    for num2, g2 in enumerate(nonfiction):
        if num2 == 0:
            low2 = genre_check(genre, g2)
            index2 = num2
        elif genre_check(genre, g2) < low2:
            low2 = genre_check(genre, g2)
            index2 = num2
    if low1 < low2:
        return low1, index1, 'Fiction'
    elif low2 < low1:
        return low2, index2, 'Nonfiction'
    elif low1 == low2:
        return None, None, None


if __name__ == "__main__":
    setup_csv()
    titles = []
    num = int(input("how many books: "))
    for _ in range(num):
        titles.append(input('book title: '))
    for title in titles:
        book = GoogleBook(title = title)
        input_data(book)
