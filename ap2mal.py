#!/usr/bin/python
#This script will take your anime-planet.com username and add your list to MAL using its API
#Errors are output so you can enter those manually
#set debug = True to get more information on all of your entries
#Additional info and packages:
#  Python 3.3.3 - http://python.org/download/
#  BeautifulSoup4 - http://www.crummy.com/software/BeautifulSoup/#Download
#Tips:
# * You can leave your MAL username empty if it's the same as on AnimePlanet.
# * To install BeautifulSoup unpack it anywhere and type "setup.py install" in the console from that folder.
# * In order to successfully import the exported Anime-Planet animelist to MAL, first export MAL animelist,
#    and copy the <myinfo> block just after <myanimelist> tag.


from bs4 import BeautifulSoup,NavigableString
import urllib.request,urllib.parse,base64,sys,re,codecs
import xml.etree.ElementTree as et

debug = False
delimiter = "\t"
userAgent = "Mozilla/5.0 (Windows NT 6.2; Win64; x64;) Gecko/20100101 Firefox/20.0"

print("This script will export your anime-planet.com anime list to myanimelist.net")

username = input("Enter your AP username: ")
malusername = input("Enter your MAL username: ")
if (malusername == ""): malusername = username
malpassword = input("Enter your MAL password: ")

baseURL = "http://www.anime-planet.com/users/%s/anime" % username
apiURL = "http://myanimelist.net/api/anime/search.xml"
apiURLadd = "http://myanimelist.net/api/animelist/add/%s.xml"
apiURLupdate = "http://myanimelist.net/api/animelist/update/%s.xml"

passStr = str("%s:%s" % (malusername, malpassword)).replace("\n", "")
authString = str(base64.b64encode(bytes(passStr, "utf-8")), "utf-8")
if debug: print("MAL authorization hash: " + authString)

#Try to get HTML of first page.
try:
    req = urllib.request.Request(baseURL)
    req.add_header("User-Agent",  userAgent)
    html = BeautifulSoup(urllib.request.urlopen(req).read(), "html.parser")
    pageNumber = int (html.find("li","next").findPrevious("li").next.contents[0])
    #if your list is only one page, uncomment the line below and comment the line above
    #pageNumber = int (html.find('li','next').findPrevious('li').contents[0])
except BaseException as e:
    print("Request to " + baseURL + " failed. " +str(e))
    raise SystemExit

print("Processing AP list and requesting data from MAL...")

#loop through all of your pages
for i in range(1,pageNumber+1):
    try:
        req = urllib.request.Request(baseURL + "?" + urllib.parse.urlencode({"page": str(i)}))
        if debug: print("Calling URL:" + baseURL + "?" + urllib.parse.urlencode({"page": str(i)}))
        req.add_header("User-Agent",  userAgent)
        html = BeautifulSoup(urllib.request.urlopen(req).read(), "html.parser")
    except BaseException as e:
            print("Request to " + baseURL + "?" + urllib.parse.urlencode({"page": str(i)}) + " failed. " +str(e))
            raise SystemExit
    #loop through all of the anime posters on page i
    for animeItem in html.findAll("li",class_="card"):
        animeItem = BeautifulSoup(animeItem.renderContents(), "html.parser")
        animeName = "" + animeItem.a.div.img["alt"]
        #pretty apostophe was breaking things
        animeName = animeName.replace("’","'")
        queryTitle = ""
        try:
            titlereq = urllib.request.Request(apiURL + "?" + urllib.parse.urlencode({ "q" : animeName }))
            titlereq.add_header("Authorization", "Basic %s" % authString)
            titlereq.add_header("User-Agent",  userAgent)
            queryTitle = urllib.request.urlopen(titlereq).read().decode("utf-8")
            #I think this removes the synopsis for some reason, whatever
            queryTitle = re.sub(r"(?is)<synopsis>.+</synopsis>", "", queryTitle)
        except BaseException as e:
            print("Anime: " + animeName)
            print("Request to " + apiURL + "?" + urllib.parse.urlencode({ "q" : animeName }) + " failed. " +str(e))
            raise SystemExit
        #get the status, which is now a class name
        status = animeItem.find("div","statusArea").span["class"][0]
        formattedStatus = ""
        if status=="status6":
            formattedStatus = "won't watch"
            status="4"
        elif status=="status3":
            formattedStatus = "dropped"
            status="4"
        elif status=="status4":
            formattedStatus = "want to watch"
            status="6"
        elif status=="status5":
            formattedStatus = "stalled"
            status="3"
        elif status=="status1":
            formattedStatus = "watched"
            status="2"
        elif status=="status2":
            formattedStatus = "watching"
            status="1"
        search = ""
        try:
            if queryTitle != '':
                search = et.fromstring(queryTitle)
                if debug: print("================")
                if debug: print("Anime: " + animeName)
                if debug: print(apiURL + "?" + urllib.parse.urlencode({ "q" : animeName }))
            else:
                # This item failed to get a title match
                if ":" not in animeName:
                    print("================")
                    print("Anime: " + animeName)
                    print(apiURL + "?" + urllib.parse.urlencode({ "q" : animeName }))
                    print("Search failed; no match found.")
                    print("Status: " + formattedStatus)
                    continue
                else:
                    #try truncated name for initial search
                    formattedName = animeName.split(":")[0]
                    try:
                        titlereq = urllib.request.Request(apiURL + "?" + urllib.parse.urlencode({ "q" : formattedName }))
                        titlereq.add_header("Authorization", "Basic %s" % authString)
                        titlereq.add_header("User-Agent",  userAgent)
                        queryTitle = urllib.request.urlopen(titlereq).read().decode("utf-8")
                        #I think this removes the synopsis for some reason, whatever
                        queryTitle = re.sub(r"(?is)<synopsis>.+</synopsis>", "", queryTitle)
                    except BaseException as e:
                        print("Anime: " + animeName)
                        print("Request to " + apiURL + "?" + urllib.parse.urlencode({ "q" : formattedName }) + " failed. " +str(e))
                        raise SystemExit
                    if queryTitle != '':
                        search = et.fromstring(queryTitle)
                        if debug: print("================")
                        if debug: print("Anime: " + animeName)
                        if debug: print(apiURL + "?" + urllib.parse.urlencode({ "q" : formattedName }))
                    else:
                        # This item failed to get a title match
                        print("================")
                        print("Anime: " + animeName)
                        print(apiURL + "?" + urllib.parse.urlencode({ "q" : formattedName }))
                        print("Search failed; no match found.")
                        print("Status: " + formattedStatus)
                        continue
                continue
        except BaseException as e:
            print("Decoding of anime data failed. Error: " +str(e))
            # for adding anime manually
            continue
        localName = animeName.lower().replace(":","").replace("(","").replace(")","")
        animeID = ""
        episodeCount = ""
        #check all results for an id
        for entry in search.findall("./entry"):
            try:
                if entry.find("id") is not None and entry.find("id").text.strip()!="":
                    if entry.find("title") is not None and localName in entry.find("title").text.lower().replace(":","").replace("(","").replace(")",""):
                        animeID=entry.find("id").text
                        episodeCount = entry.find("episodes").text
                        break
                    elif entry.find("english") is not None and localName in entry.find("english").text.lower().replace(":","").replace("(","").replace(")",""):
                        animeID=entry.find("id").text
                        episodeCount = entry.find("episodes").text
                        break
                    elif entry.find("synonyms") is not None and localName in entry.find("synonyms").text.lower().replace(":","").replace("(","").replace(")",""):
                        animeID=entry.find("id").text
                        episodeCount = entry.find("episodes").text
                        break
            except:
                continue
        if animeID=="":
            print("No MAL ID found in returned results.")
            continue
        if debug: print("MAL ID = " + animeID)

        xmlData = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        xmlData += "<entry>\n"

        if status == "4" or status == "6":
            xmlData += "\t<episode></episode>\n"
        #had to include watched here because there's no way to get the # of eps anymore from AP
        elif status == "2":
            xmlData += "\t<episode>" + episodeCount + "</episode>\n"
        else:
            xmlData += "\t<episode>"+ animeItem.find("div","statusArea").text.replace("eps","").replace("ep","").replace("\t", "").replace("\n", "").replace("\r", "").replace(" ", "") +"</episode>\n"
        xmlData += "\t<status>" + status +"</status>\n"
        try:
            rating = animeItem.find("div", attrs={"class": "ttRating"}).text;
            xmlData += "\t<score>" + str(int(float(rating)*2)) + "</score>\n"
        except:
            xmlData += "\t<score></score>\n"
            continue
        xmlData += "\t<downloaded_episodes></downloaded_episodes>\n"
        xmlData += "\t<storage_type></storage_type>\n"
        xmlData += "\t<storage_value></storage_value>\n"
        xmlData += "\t<times_rewatched></times_rewatched>\n"
        xmlData += "\t<rewatch_value></rewatch_value>\n"
        xmlData += "\t<date_start></date_start>\n"
        xmlData += "\t<date_finish></date_finish>\n"
        xmlData += "\t<priority></priority>\n"
        xmlData += "\t<enable_discussion></enable_discussion>\n"
        xmlData += "\t<enable_rewatching></enable_rewatching>\n"
        xmlData += "\t<comments></comments>\n"
        xmlData += "\t<fansub_group></fansub_group>\n"
        xmlData += "\t<tags></tags>\n"
        xmlData += "</entry>\n"

        params = {'id' : animeID, 'data' : xmlData}
        isAdded = False
        try:
            if debug:
                print("Trying to add anime... ")
            url = urllib.request.Request(apiURLadd % animeID, urllib.parse.urlencode(params).encode("utf-8"))
            url.add_header("Authorization", "Basic %s" % authString)
            url.add_header("User-Agent",  userAgent)
            urllib.request.urlopen(url)
            isAdded = True
        except:
            isAdded = False
        if not isAdded:
            try:
                if debug:
                    print("\rTrying to update anime... ")
                url = urllib.request.Request(apiURLupdate % animeID, urllib.parse.urlencode(params).encode("utf-8"))
                url.add_header("Authorization", "Basic %s" % authString)
                url.add_header("User-Agent",  userAgent)
                urllib.request.urlopen(url)
                isAdded = True
            except:
                isAdded = False
        if debug:
            if isAdded: sys.stdout.write("OK\n")
            else: sys.stdout.write("FAILED\n")
            sys.stdout.flush()

print("\nDone")