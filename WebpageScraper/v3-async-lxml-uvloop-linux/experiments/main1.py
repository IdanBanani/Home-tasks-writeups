# import asyncio, threading


# loop = asyncio.get_event_loop()
# # threading.Thread(target=loop.run_forever).start()

# async def do_job(url):
#     # do job here
#     print(f'doing job... {url}')
    

# async def get_urls(): # send task to event loop without blocking
#     tasks = []
#     for url in ['a', 'b', 'c']:
#         tasks.append(await asyncio.run_coroutine_threadsafe(    do_job(url), loop) )

#     result = await asyncio.gather(*tasks)
#     print(result)



# async def main():
#     await get_urls()


# asyncio.run(main())

a = 1
breakpoint()
print('exiting...')



# Async for loop; Get image async -> every iteration push the result as job to other async function


# loop = asyncio.get_event_loop()
# threading.Thread(target=loop.run_forever).start()

# async def do_job(url):
#     pass
#     # do job here

# async def get_urls(): # send task to event loop without blocking
#     tasks = []
#     async for url in ['a', 'b', 'c']:
#         tasks.append(
#             asyncio.create_task(do_job())
#         )
#     asyncio.gather(*tasks)

