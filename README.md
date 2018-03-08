# chatscript-in-docker
Minimal ChatScript Engine ready to launch your bot

You can also pull directly the Docker image from this [Docker Hub](https://hub.docker.com/r/dleclercq/chatscript-in-docker/) repo.

Based [ChatScript 8.1](https://github.com/chatscriptnlp/ChatScriptNLP), this image has all core files to run your bot in English.

# Build

Building the image is as easy as cloning the repo and building using the Dockerfile.

```
$ git clone https://github.com/Mirrdhyn/chatscript-in-docker.git
$ cd chatscript-in-docker
$ docker build -t dleclercq/chatscript-in-docker:latest .
```

# Kick-start

To launch your bot, you have to mount your folder where you have all your top files and filesBuild to the bot data inside this image.
Better an example than a long speech :

```$ docker run -t -i -p 1024:1024 -v C:\cs\MyBot\:/data/ChatScriptNLP/RAWDATA -v C:\cs\BOTS\BNPCIBECH\USERS\:/data/ChatScriptNLP/USERS -v C:\cs\BOTS\BNPCIBECH\LOGS\:/data/ChatScriptNLP/LOGS dleclercq/chatscript-in-docker:latest```

You can do this on Windows Docker as well. _Mine is working on my Windows laptop._

The option `p` is to plug my localhost port 1024 to the internal 1024 port of ChatScript server.

The option `v` is to mount my local code inside the `RAWDATA` folder where my bot will be running.

The two more options `v` are used to link `USERS` and `LOGS` files produced by the CS engine to your local machine. Using these options could be useful if you would like to save history and logs of your users to another server, a SAN for instance. You can scale up CS engine with Docker and Load Balancer (orchestrator) and use the same user logs.

The path inside this image is `/data/` where all ChatScript files are stored. You can now reflect this path to your files1.txt (for instance) to link your build bot to this Docker image.

# Connect clients

When you are ready, you can now connect any ChatScript client, or send your packets to the socket. If, like me, you run the ChatScript.exe, you have just to add the option `client=localhost:1024` and you should have your engine responding to you.
Easily now, you can `:build 0` and `:build MyBot` to begin a new conversation with your bot in Docker.

# Connect to CS Engine using bash

```$ docker exec -it chatscript /bin/bash```

Then, you have a bash command line ready to change everything inside.