![1553 1593611237](https://user-images.githubusercontent.com/26879273/145428275-43886795-c540-4b16-a527-1f766b733185.png)

# The task definition

Using the wikipedia page for List of animal names, write a python program that will output all of the “collateral adjectives” and all of the “animals” which belong to it.  
If an animal has more than one collateral adjective, use all of them (mentioning it more than once).

Bonus work (choose whether and as many as you like):
- Download the picture of each animal into /tmp/ and add a local link when displaying the animals.
- Write at least 2 test cases for the code you just wrote.
- Output your results to an html file.

Tips: Feel free to use BeautifulSoup and Requests, and please avoid pandas if you can.  

# How to approach this?
First of all, we will translate the system/functional requirements into coding terms.
Lets try to recognize the elements and divide the work into subtasks:

![33311](https://user-images.githubusercontent.com/26879273/145437484-5cdc6cc8-5ccd-4793-8dbf-920570ab27d1.png)

In our main/worker/daemon thread do the following:
----------------------------------------------------------------
1. Download the main wiki webpage "object" 
2. Create a beautiful soup object form its content/text 
3. Extract the relevant table element 

Since the information is arranged in a HTML Table rows (There's no direct access to coloumns), we will do the same operation for all of the data rows:  

#TODO: If the table was gigantic, would it affect our program due to memory considarations? - (getting the whole page/table content at once vs reading it in chunks) )


Given a row:  
--
1. Extract & Save the items of our interest: Animal name, its image link (Either average quality image link using a tool like Selenium webdriver to hover over the animal name to make a pop-up appear OR a high resolution one linked from the animal's wikipedia page) and its Collateral adjective to a local storage / DB in which the key is the Collateral adjective and the values are references to its matching animals records (In our case, they contain name + path to its locally hosted image)
2. Download its animal image (direct/indirect) to folder /tmp (Linux) or %temp% on Windows
3. Save the path to the downloaded image in the local DB (to the animal record)

Once we finished updating the Database:
--
1. Plot to the screen the DB "Group by" query as instructed
2. Crate an HTML format output file showcasing the results including images

# Performance considarations:
Implementing this program naively will cost us a lot of wasted time.
The steps we can take in order to do more work in less time:

We will Identify what specific tasks should be done sequentially (non-asynchronously), what tasks requests can be done asynchronously (not waiting for a similar request to receive its respone before dispatching another one) and where can we implement concurency/parallelism if we wish to enable scaleability. 



1. Use a single shared session for all of the web requests to the wikipedia domain  
   #TODO: Speed-wise, Does it matter if we communicate with a single domain or more than one?  
         Should I change the settings of the web-requests session object?     
2. Use a multi-processing pool - distribute the independent tasks of parsing the rows between them (These are "CPU-bounded" jobs), each process doesn't need to know about/have access to the rows processed by other processes (which fits the fact that processes don't share memory by default)
3. Transform the rest of the synchronic web requests (Getting other wiki pages + downloding animals images) and writing to files operations into async ones
4. Wait for all tasks & processes to finish
5. Start plotting the output of the "group_by" request from our DB While creating the html output at same time (they are independent on each other)

**Time complexity:**  [#TODO: update]
N = Number of listed animals on the wikipedia page, M = total number of collateral adjectives
Async solution: O(N) + O(Max(image_download_times)) [The async part]  
Async+Multiprocessing solution (theoretically better) : O(Max(CPU_BOUND_TASKS))+O(Max(IO_BOUND_TASKS))

**Space complexity:** [#TODO: update] O(N) [One record for each animal]

# Design & rules of thumbs
Use one or more from the well trusted software design principles
(SOLID,Clean-code, KISS etc.) for the main business logic.

**Premature optimization is the root of all evil (or at least most of it) in programming** - We'll aim to first build something that works, and only then try to improve it if there's a need.  

But there's a trade-off in our case:  
While fixing bugs is easier with a single threaded synchronic application (Otherwise debugging might go crazy with bouncing back and forth between breakpoints/asyncio mini-threads), Identifying the anomalies/errors where edge cases are not handled properly is much faster when using async programming for executing all the requests in a short time (The main bottleneck here is the Network IO bound operations) 

Using OOP in Python is a matter of taste and not a must.

----------------------------------------------------------------
# Results:
- Latest Async implementation -**114 seconds < 2 minutes including downloading all the images (677 MB)**, 1.5 sec for execitopm with caching enabled and about 30  seconds or less for getting all animals pages for extracting images links without downloading the images = getting the links of the images even though we won't download them (I didn't benchmark it after optimizations due to code modifications such as caching images names according to the animal name) .  
- The full async implementation (v3) gave about x2 speedup.

## Running the code (V3-Async On Linux):
```
pip install pipenv  
pipenv shell  
pipenv install -r requirements.txt
python3 main.py
```
---------------------
## TODO: 
- Can we benefit from inheritance (OOP) in this case?
- How would you give the "requests sender function" access to the session object in a smarter way? (sharing a datastructure without using global variable / class attribute)   
- Is it possible here to seperate the API from the implementation?
- Look for remaining places where we can seperate generic "utilities" from the specific "Wikipedia"/"Animals page parser" code (for future code-reuse)

## Testing
Pytest might won't work properly with async code.
* pytest-asyncio (v0.16.0)

## Optimizations
* grequests - too old/unstable but seems to be a "quick and dirty" solution
* multiprocessing.apply_async / or equivalent from the more recommended: concurrent.futures.ProcessPoolExecutor() - [Documentation](https://docs.python.org/3/library/multiprocessing.html), [StackOverflow thread](https://stackoverflow.com/questions/8533318/multiprocessing-pool-when-to-use-apply-apply-async-or-map) - seems to solve the constraint of having to change the whole code in order to work asynchronously.
* aiohttp - used here as an async http requests library
* aiofiles - used here as an async File I/O operation library 
* uvloop - using it's event-loop instead of asyncio's main_loop (more suitable for production environment) [Doesn't support Windows!]
* aiomultiprocess (v0.9.0) - ?
* [unsync - Unsynchronize asyncio by using an ambient event loop, or executing in separate threads or processes.](https://github.com/alex-sherman/unsync/)
* Scrapy - (For large scale project. Not everyone likes this library) - An open source and collaborative framework for extracting the data you need from websites. In a fast, simple, yet extensible way. Scrapy is a fast high-level web crawling and web scraping framework, used to crawl websites and extract structured data from their pages. It can be used for a wide range of purposes, from data mining to monitoring and automated testing.


## Reducing boilerplate code / Doing it easier & faster and maybe even give better performance
* Trio
* AnyIO 
* Fastapi (while probabely having to run it as a **web server app** due to the "routing requests" API mechanism)
* [Example for using wikipediaapi library + grequests](https://github.com/DanOren/Web_Scraping_Project_ITC/blob/main/URL_scraper.py)
* [non-official aiocollections](https://github.com/bharel/aiocollections)

## Trade-offs


## Appendix
#### System design principles & production level programming with Python :
- [Advanced system design - TAU Course by Dan Gittik](https://advanced-system-design.com/lessons/)  
- [Source code for the course excercises](https://github.com/advanced-system-design)  
### The aiomultiprocess pitch:  
![image](https://user-images.githubusercontent.com/26879273/145200762-d4ac346c-a7d0-4fa1-8979-0f34eb351f82.png)


