TITLE = 'RT America'
PREFIX = '/video/rtusa'
ICON = 'icon-default.png'

RT_BASE = 'https://www.rt.com'
RT_NEWS = "https://www.rt.com/bulletin-board/news/"
RT_USANEWS = "https://www.rt.com/bulletin-board/rt-america/"
RT_SHOWS = 'https://www.rt.com/shows/'

LIVE_FEED = 'https://secure-streams.akamaized.net/%s/index2500.m3u8'
LIVE_OPTIONS = [("RT News Live", "rt"), ("RT USA Live", "rt-usa"), ("RT Documentary Live", "rt-doc"), ("RT UK Live", "rt-uk"), ("RT Arabic Live", "rt-arab")]

VIDEO_SHOWS = ('In Context', 'Larry King Now', 'Off the grid', 'Politicking')

####################################################################################################
def Start():

    ObjectContainer.title1 = TITLE
    DirectoryObject.thumb = R(ICON)
    VideoClipObject.thumb = R(ICON)
    HTTP.CacheTime = CACHE_1HOUR
 
####################################################################################################
@handler(PREFIX, TITLE, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()
  
    oc.add(DirectoryObject(key=Callback(Shows, title='Shows'), title='Shows')) 
    oc.add(DirectoryObject(key=Callback(LiveFeeds, title='Live Feeds'), title='Live Feeds')) 

    return oc

####################################################################################################
# to produce shows
@route(PREFIX + '/shows')
def Shows(title):

    oc = ObjectContainer(title2=title)
    data = HTML.ElementFromURL(RT_SHOWS)

    # The news programs are not linked as shows, so we hard code these into the list 
    # We pull thumbs for these news shows from the first video link for each at the bottom of the page
    thumb1 = data.xpath('//a[contains(@href, "shows/news/")]/img/@src')
    thumb2 = data.xpath('//a[contains(@href, "shows/rt-america/")]/img/@src')

    oc.add(DirectoryObject(key=Callback(ShowVideos, title='RT News', url=RT_NEWS), title='RT News', thumb=Resource.ContentsOfURLWithFallback(url=thumb1))) 
    oc.add(DirectoryObject(key=Callback(ShowVideos, title='RT America News', url=RT_USANEWS), title='RT America News', thumb=Resource.ContentsOfURLWithFallback(url=thumb2))) 

    for show in data.xpath('//ul[@class="card-rows"]/li'):

        url = RT_BASE + show.xpath('.//a//@href')[0]
        title = show.xpath('.//a/text()')[0].strip()
        summary = show.xpath('.//div[contains(@class, "card__summary")]//text()')[0]
        thumb = show.xpath('.//img//@src')[0]

        oc.add(DirectoryObject(key=Callback(ShowVideos, title=title, url=url), title=title, summary=summary, thumb=Resource.ContentsOfURLWithFallback(url=thumb)))

    oc.add(DirectoryObject(key=Callback(ArchiveShows, title='Archived Shows'), title='Archived Shows')) 

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no shows to list right now.")
    else:
        return oc

####################################################################################################
# To get videos for shows
@route(PREFIX + '/showvideos')
def ShowVideos(title, url):

    oc = ObjectContainer(title2=title)
    data = HTML.ElementFromURL(url)
    show_title = title

    for video in data.xpath('//div[contains(@class, "js-listing")]/ul/li'):

        # See if the link is a video link
        try:
            url = RT_BASE + video.xpath('.//div[contains(@class, "image_type_video")]/a//@href')[0]
        except:
            # Check the show list of those that have videos that are not the proper link format
            if show_title in VIDEO_SHOWS:
                url = RT_BASE + video.xpath('.//a//@href')[0]
            else:
                continue

        title = video.xpath('.//a/text()')[0].strip()

        try: summary = video.xpath('.//div[contains(@class, "card__summary")]//text()')[0]
        except: summary = ''

        try: thumb = video.xpath('.//img//@src')[0]
        except: thumb = ''

        oc.add(VideoClipObject(
            url = url, 
            title = title,
            summary = summary,
            thumb =  Resource.ContentsOfURLWithFallback(url=thumb)
        ))

    # pagination
    more_url = data.xpath('//a[contains(@class, "js-listing__more")]/@data-href')[0]
    if more_url:
        oc.add(NextPageObject(key=Callback(ShowVideos, title=show_title, url=RT_BASE + more_url), title="More..."))

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no videos for this show.")
    else:
        return oc

####################################################################################################
# to produce live feeds
@route(PREFIX + '/livefeeds')
def LiveFeeds(title):

    oc = ObjectContainer(title2=title)

    for (title, ch_code) in LIVE_OPTIONS:

        ch_m3u8 = LIVE_FEED % (ch_code)
        oc.add(CreateVideoClipObject(title=title, ch_m3u8=ch_m3u8))

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no feeds to list right now.")
    else:
        return oc

####################################################################################################
@route(PREFIX + '/createvideoclipobject', include_container=bool)
def CreateVideoClipObject(ch_m3u8, title, include_container=False, **kwargs):

    videoclip_obj = VideoClipObject(
        key = Callback(CreateVideoClipObject, ch_m3u8=ch_m3u8, title=title, include_container=True),
        rating_key = ch_m3u8,
        title = title,
        items = [
            MediaObject(
                parts = [
                    PartObject(key=HTTPLiveStreamURL(ch_m3u8))
                ],
                protocol = 'hls',
                container = 'mpegts',
                video_resolution = 720,
                video_codec = VideoCodec.H264,
                audio_codec = AudioCodec.AAC,
                audio_channels = 2,
                optimized_for_streaming = True,
            )
        ]
    )

    if include_container:
        return ObjectContainer(objects=[videoclip_obj])
    else:
        return videoclip_obj

####################################################################################################
# to produce archived shows
@route(PREFIX + '/archiveshows')
def ArchiveShows(title):

    oc = ObjectContainer(title2=title)
    data = HTML.ElementFromURL(RT_SHOWS)

    for show in data.xpath('//p[@class="archive-links"]/a'):

        url = RT_BASE + show.xpath('./@href')[0]
        title = show.xpath('.//text()')[0].strip()

        oc.add(DirectoryObject(key=Callback(ShowVideos, title=title, url=url), title=title))

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no shows to list right now.")
    else:
        return oc
