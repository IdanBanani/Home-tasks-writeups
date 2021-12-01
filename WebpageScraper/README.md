# The task definitions

Using the wikipedia page for List of animal names, write a python program that will output all of the “collateral adjectives” and all of the “animals” which belong to it. If an animal has more than one collateral adjective, use all of them (mentioning it more than once).

- How much time did it take you to write this ?
- What’s the time complexity of the program you just wrote ?

Bonus work (choose whether and as many as you like):
- Download the picture of each animal into /tmp/ and add a local link when displaying the animals.
- Write at least 2 test cases for the code you just wrote.
- Output your results to an html file.

Tips: Feel free to use BeautifulSoup and Requests, and please avoid pandas if you can.  

# How to approach this?
First of all, we will translate the system/functional requirements into coding terms.

Lets try to recognize the elements and divide the work into subtasks:

In our main thread, do the following:
----------------------------------------------------------------
1. Download the main wiki webpage "object" 
2. Create a beautiful soup object form its content ("raw bytes") or text (or try working with json format?)
3. Extract the relevant table element (#TODO: If the table was gigantic, would it affect our strategy due to memory considarations?)

Since the information is arranged in HTML rows (There's no direct access to coloumns), we will do the same operation for all of the data rows:  
----
Given a row:  
--
1. Extract & Save the items of our interest: Animal name, its image link (Either average quality image link using a tool like Selenium webdriver to hover over the animal name to make a pop-up appear OR a high resolution one linked from the animal's wikipedia page) and its Collateral adjective to a local storage / DB in which the key is the Collateral adjective and the values are references to its matching animals records (In our case, they contain name + link to its locally hosted image)
2. Download its animal image (direct/indirect) to folder /tmp (Linux) or %temp% on Windows
3. Save the link to the downloaded image in the local DB (to the animal record)

Once we finished updating the Database:
--
1. Plot to the screen the DB "Group by" query as instructed
2. Crate a HTML format output file showcasing the results

# Performance considarations:
Implementing this program naively will cost us a lot of wasted time.
The steps we can take in order to do more work in less time:

We will Identify what specific tasks should be done sequentially (non-asynchronously), what tasks requests can be done asynchronously (not waiting for a similar request to receive its respone before dispatching another one) and where can we implement concurency/parallelism if we wish to enable scaleability. 

#TODO: Does it matter if we communicate with a single domain or more than one?  
#TODO: Does creating a number of sessions equal to the number of cores makes things better or worse?  
1. Use a single shared session for all of the web requests to the wikipedia domain
2. Use a multi-processing pool - distribute the independent tasks of parsing the rows between them (These are "CPU-bounded" jobs), each process doesn't need to know about/have access to the rows processed by other processes (which fits the fact that processes don't share memory by default)
3. Transform the rest of the synchronic web requests (Getting other wiki pages and animals images) into async ones
4. Wait for all tasks & processes to finish
5. Start plotting the output of the "group_by" request from our DB While. Try to create the html output at same time.

N = Number of listed animals on the wikipedia page

Time complexity:  O(N) + O(Max(image_download_times)) [The async part]
Space complexity: O(N) [One record for each animal]

# Design & rules of thumbs
Use one or more from the well trusted software design principles
(SOLID,Clean-code, KISS etc.) for the main business logic.

**Premature optimization is the root of all evil (or at least most of it) in programming** - We'll aim to first build something that works, and only then try to improve it if there's a need.  
But there's a trade-off in our case:  
While fixing bugs is easier with a single threaded synchronic application (Otherwise Pycharm might go crazy with bouncing back and forth between breakpoints), Identifying the anomalies/errors where edge cases are not handled properly is much faster when using async programming for executing all the requests in a short time while watching the log output (The main bottleneck here is the IO bound operations) 

Using OOP in Python is a matter of taste and not a must.
#TODO: How would you give the "request sender function" access to the session object in a smart way without using classes?

#TODO: Can we benefit from inheritance? what about seperating the API from the implementation?

## Testing
Pytest might don't work properly with async code.
* pytest-asyncio (v0.16.0)

## Optimizations
* aiohttp
* aiofiles
* uvloop loop instead of asyncio's main_loop (more suitable for production environment)
* aiomultiprocess (v0.9.0)
* [unsync - Unsynchronize asyncio by using an ambient event loop, or executing in separate threads or processes.](https://github.com/alex-sherman/unsync/)

## Reducing boilerplate code / Doing it easier & faster
* Trio
* AnyIO 
* Fastapi (while probabely having to run it as a **web server app** due to the "routing requests" API mechanism)

## Trade-offs

