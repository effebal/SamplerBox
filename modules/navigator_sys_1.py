#  SamplerBox Navigator
#
#  author:    Alex MacRae (alex.finlay.macrae@gmail.com)
#  url:       https://github.com/alexmacrae/
#  license:   Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
#
#  samplerbox2.py: Main file
#

#########################################
# Import
#
#########################################
import threading
import time

import configparser

import configparser_samplerbox as cs
import globalvars as gv
import loadsamples as ls
import menudict


def write_setlist(list_to_write):
    print('-= WRITING NEW SETLIST =-')
    setlist = open(gv.SETLIST_FILE_PATH, "w")
    list_to_write = list(filter(None, list_to_write))  # remove empty strings / empty lines
    for song in list_to_write:
        setlist.write(song + '\n')
    setlist.close()


def findMissingFolders():
    # Check to see if the song name in the setlist matches the name of a folder.
    # If it doesn't, mark it by prepending an *asterix and rewrite the setlist file.

    songsInSetlist = open(gv.SETLIST_FILE_PATH).read().splitlines()
    songsInSetlist = list(filter(None, songsInSetlist))  # remove empty strings / empty lines
    changes = False
    k = 0
    for song_name in songsInSetlist:
        i = 0
        for song_folder_name in gv.SONG_FOLDERS_LIST:

            if (song_name == song_folder_name):
                # print(song_name + ' was found')
                break
            elif (song_name.replace('* ', '') == song_folder_name):
                # print(song_name + ' was found - previous lost')
                songsInSetlist[k] = song_name.replace('* ', '')
                # break
            else:
                if (i == len(gv.SONG_FOLDERS_LIST) - 1):
                    print(song_name + ' WAS NOT FOUND. ')
                    songsInSetlist[k] = '* ' + song_name.replace('* ', '')
                    changes = True
                    break

            i += 1
        k += 1

    if (changes):
        write_setlist(songsInSetlist)
    else:
        print('-= No missing folders detected =-\n')


def findAndAddNewFolders():
    # Check for new song folders and add them to the end of the setlist

    songsInSetlist = open(gv.SETLIST_FILE_PATH).read().splitlines()
    songsInSetlist = list(filter(None, songsInSetlist))  # remove empty strings / empty lines
    changes = False

    if (set(songsInSetlist).intersection(gv.SONG_FOLDERS_LIST) != len(gv.SONG_FOLDERS_LIST) and len(
            songsInSetlist) != 0):

        for song_folder_name in gv.SONG_FOLDERS_LIST:
            i = 0
            for song_name in songsInSetlist:
                if (song_folder_name == song_name):
                    break
                elif (i == len(songsInSetlist) - 1):
                    print (song_folder_name + ' - NEW FOLDER')
                    changes = True
                    songsInSetlist.append(song_folder_name)
                    break

                i += 1
    elif (len(songsInSetlist) == 0):
        songsInSetlist = gv.SONG_FOLDERS_LIST
        changes = True
        print ('Setlist empty - adding all foldings')

    # print(songsInSetlist)
    if (changes):
        write_setlist(songsInSetlist)
    else:
        print('-= No new folders found =-\n')

        # ______________________________________________________________________________


def removeMissingSetlistSongs():
    songsInSetlist = open(gv.SETLIST_FILE_PATH).read().splitlines()
    i = 0
    for song in songsInSetlist:
        if ('* ' in song):
            del songsInSetlist[i]
            write_setlist(songsInSetlist)
        i += 1


# ______________________________________________________________________________
# On startup detect missing folders and add any new ones found                
findMissingFolders()
removeMissingSetlistSongs()
findAndAddNewFolders()


# ______________________________________________________________________________


class Navigator:
    menu = menudict.menu

    state = None
    menuCoords = [0]
    menuPointer = 0
    function = None
    config = configparser.ConfigParser()

    def __init__(self, initState):
        Navigator.state = initState
        self.loadState(Navigator.state)

    def loadState(self, theClass):
        Navigator.state = theClass()

    def getMenuPathStr(self):

        menuMsg = self.getMenu().get(self.menuPointer).get('name')

        return menuMsg

    def getMenu(self, mc=None):
        if not mc:
            mc = Navigator.menuCoords
        menu = Navigator.menu.get('submenu')
        i = 0
        while i < len(mc):
            if i > 0:
                menu = menu.get(mc[i - 1]).get('submenu')
            i += 1
        return menu


# ______________________________________________________________________________





class PresetNav(Navigator):
    def __init__(self):

        print '-= Preset world =-'
        gv.displayer.menu_mode = gv.displayer.DISP_PRESET_MODE
        gv.displayer.disp_change(changed_var='preset')
        # gv.displayer.disp_change('preset') # already called in ActuallyLoad()

    def right(self):
        gv.preset += 1
        gv.displayer.LCD_SYS.reset_after_timeout()
        gv.currvoice = 1
        if (gv.preset >= gv.NUM_FOLDERS):
            gv.preset = 0
        gv.displayer.menu_mode = gv.displayer.DISP_PRESET_MODE  # need to set if interrupted by utils left/right
        gv.displayer.disp_change('preset')
        ls.LoadSamples()

    def left(self):
        gv.preset -= 1
        gv.displayer.LCD_SYS.reset_after_timeout()
        gv.currvoice = 1
        if (gv.preset < 0):
            gv.preset = gv.NUM_FOLDERS - 1
        gv.displayer.menu_mode = gv.displayer.DISP_PRESET_MODE  # need to set if interrupted by utils left/right
        gv.displayer.disp_change('preset')
        ls.LoadSamples()

    def enter(self):
        self.loadState(MenuNav)

    def cancel(self):  # can remove empty class methods
        self.loadState(UtilsView)

        # hd44780_20x4.TimeOut = hd44780_20x4.TimeOutReset
        # hd44780_20x4.resetModes()
        # hd44780_20x4.inSysMode = True
        # eg CPU/RAM, battery life, time, wifi/bluetooth status


# ______________________________________________________________________________





class UtilsView(PresetNav):
    def __init__(self):

        print '-= Utils view =-'
        gv.displayer.menu_mode = gv.displayer.DISP_UTILS_MODE
        gv.displayer.disp_change(changed_var='util')
        self.timeout_start = time.time()
        self.UtilsThread = threading.Thread(target=self.display_utils)
        self.UtilsThread.daemon = True
        self.UtilsThread.start()

    def display_utils(self):
        looping = True
        while looping:
            now = time.time()
            if (now - self.timeout_start) < 3:
                gv.displayer.disp_change(changed_var='util')
                time.sleep(0.25)
            else:
                self.loadState(PresetNav)
                looping = False

            time.sleep(0.25)

    # def right(self):
    #     pass
    #
    # def left(self):
    #     pass

    def enter(self):
        self.loadState(MenuNav)

    def cancel(self):  # can remove empty class methods
        self.timeout_start = time.time()

        # hd44780_20x4.TimeOut = hd44780_20x4.TimeOutReset
        # hd44780_20x4.resetModes()
        # hd44780_20x4.inSysMode = True
        # eg CPU/RAM, battery life, time, wifi/bluetooth status


# ______________________________________________________________________________
functionToMap = None
functionNiceName = None


class MenuNav(Navigator):
    def __init__(self):

        self.menuPointer = self.menuCoords[-1]

        gv.displayer.menu_mode = gv.displayer.DISP_MENU_MODE
        gv.displayer.disp_change(changed_var=self.getMenuPathStr(), line=1, timeout=0)
        gv.displayer.disp_change(changed_var='-' * 20, line=2, timeout=0)
        gv.displayer.disp_change(changed_var='', line=3, timeout=0)
        gv.displayer.disp_change(changed_var='', line=4, timeout=0)


    def left(self):

        if self.menuPointer > 0:
            self.menuPointer -= 1
            self.menuCoords[-1] = self.menuPointer
            gv.displayer.disp_change(self.getMenu().get(self.menuPointer).get('name'), line=1, timeout=0)

    def right(self):

        if self.menuPointer < len(self.getMenu()) - 1:
            self.menuPointer += 1
            self.menuCoords[-1] = self.menuPointer
            gv.displayer.disp_change(self.getMenu().get(self.menuPointer).get('name'), line=1, timeout=0)

    def enter(self):
        global functionToMap, functionNiceName
        menu = self.getMenu().get(self.menuPointer)
        try:
            if menu.has_key('submenu'):
                gv.displayer.LCD_SYS.display('Entering submenu for [' + menu.get('name') + ']')
                if menu.has_key('functionToMap'):
                    functionToMap = menu.get('functionToMap')
                    functionNiceName = menu.get('name')
                self.menuCoords.append(0)
                self.loadState(MenuNav)
            if menu.has_key('fn'):
                if (menu.get('fn') == 'MidiLearn') or (menu.get('fn') == 'DeleteMidiMap'):
                    self.menuCoords.append(0)
                    Navigator.state = eval(menu.get('fn'))(functionToMap, functionNiceName)
                elif isinstance(menu.get('fn'), list):
                    Navigator.state = eval(menu.get('fn')[0])(eval(menu.get('fn')[1]))  # for SelectSong
                else:
                    Navigator.state = eval(menu.get('fn'))()


        except:
            pass

    def cancel(self):
        if len(self.menuCoords) > 1:
            self.menuCoords.pop()
            self.loadState(MenuNav)
        else:
            self.loadState(PresetNav)  # this will become the gv.presets state


# ______________________________________________________________________________


class SelectSong(Navigator):
    def __init__(self, next_state):
        self.setlist_list = open(gv.SETLIST_FILE_PATH).read().splitlines()
        self.next_state = next_state
        self.display()

    def display(self):
        gv.displayer.disp_change('Select song', line=1, timeout=0)
        gv.displayer.disp_change(str(gv.preset + 1) + " " + str(self.setlist_list[gv.preset]), line=2)

    # next song
    def right(self):
        if (gv.preset < len(self.setlist_list) - 1):
            gv.preset += 1
        self.display()

    # previous song
    def left(self):
        if (gv.preset > 0):
            gv.preset -= 1
        self.display()

    def enter(self):
        self.loadState(self.next_state)

    def cancel(self):
        self.loadState(MenuNav)


# ______________________________________________________________________________

class MoveSong(Navigator):
    def __init__(self):
        self.setlist_list = open(gv.SETLIST_FILE_PATH).read().splitlines()
        self.prev_state = SelectSong
        self.display()

    def display(self):
        gv.displayer.disp_change('Moving song', line=1, timeout=0)
        gv.displayer.disp_change(str(gv.preset + 1) + " " + str(self.setlist_list[gv.preset]), line=2)

    # Move song up the setlist
    def left(self):
        if (gv.preset > 0):
            self.setlist_list[int(gv.preset)], self.setlist_list[int(gv.preset) - 1] = self.setlist_list[
                                                                                           int(gv.preset) - 1], \
                                                                                       self.setlist_list[
                                                                                           int(gv.preset)]
            gv.preset -= 1
            # write_setlist(self.setlist_list)
        self.display()

    # Move song down the setlist
    def right(self):
        if (gv.preset < len(self.setlist_list) - 1):
            self.setlist_list[int(gv.preset)], self.setlist_list[int(gv.preset) + 1] = self.setlist_list[
                                                                                           int(gv.preset) + 1], \
                                                                                       self.setlist_list[
                                                                                           int(gv.preset)]
            gv.preset += 1
            # write_setlist(self.setlist_list)
        self.display()

    def enter(self):
        write_setlist(self.setlist_list)
        Navigator.state = self.prev_state(MoveSong)

    def cancel(self):
        Navigator.state = self.prev_state(MoveSong)


# ______________________________________________________________________________

class SetlistRemoveMissing(Navigator):
    def __init__(self):

        gv.displayer.disp_change('Remove missing songs? [Y/N]', line=1, timeout=0)

    def enter(self):

        songsInSetlist = open(gv.SETLIST_FILE_PATH).read().splitlines()
        i = 0
        for song in songsInSetlist:
            if ('* ' in song):
                del songsInSetlist[i]
                write_setlist(songsInSetlist)
            i += 1

        self.loadState(MenuNav)

    def right(self):
        pass

    def left(self):
        pass

    def cancel(self):
        self.loadState(MenuNav)


# ______________________________________________________________________________


class DeleteSong(Navigator):
    def __init__(self):
        self.prev_state = eval(self.menuPosition[self.menuCoords[-1]]['fn'][0])
        self.setlist_list = open(gv.SETLIST_FILE_PATH).read().splitlines()
        gv.displayer.disp_change('Are you sure? [Y/N]', line=1, timeout=0)
        gv.displayer.disp_change('WARNING: will crash if we delete all songs', line=2)

    def enter(self):
        print self.setlist_list
        del self.setlist_list[gv.preset]
        write_setlist(self.setlist_list)
        print self.setlist_list
        if gv.preset != 0:
            gv.preset -= 1

        self.loadState(self.prev_state)

    def cancel(self):
        self.loadState(self.prev_state)


# ______________________________________________________________________________



class MidiLearn(Navigator):
    def __init__(self, functionToMap, functionNiceName):

        self.midimaps = gv.midimaps
        # src[:src.rfind(" "):] # use this to strip the port number off the end of src

        gv.learningMode = True
        self.functionToMap = functionToMap
        self.functionNiceName = functionNiceName
        self.learnedMidiMessage = None
        self.learnedMidiDevice = None
        gv.displayer.disp_change('Learning', line=1, timeout=0)
        gv.displayer.disp_change('Select a control', line=2)

    def sendControlToMap(self, learnedMidiMessage, learnedMidiDevice):
        self.learnedMidiMessage = learnedMidiMessage
        self.learnedMidiDevice = learnedMidiDevice
        gv.displayer.disp_change(
            str(learnedMidiMessage[0]) + ':' + str(learnedMidiMessage[1]) + ' ' + learnedMidiDevice,
            line=2, timeout=0)
        self.enter()  #
        # print learnedMidiMessage, learnedMidiDevice

    def enter(self):

        mm = self.midimaps

        try:
            src = self.learnedMidiDevice
            messagetype = self.learnedMidiMessage[0]
            note = self.learnedMidiMessage[1]
            messageKey = (messagetype, note)
            if src not in mm:
                mm[src] = {}  # create new empty dict key for device
                print 'Creating new device in dict'
            else:
                print 'Device is in dict - do nothing'
            if messageKey not in mm.get(src):
                mm.get(src)[messageKey] = {}  # create new empty dict key for messageKey
                print 'Creating new dict for the messageKey'
            else:
                print 'WARNING:', messageKey, 'is already mapped to:', mm.get(src).get(messageKey).get('name')
                print 'Do you want to overwrite? Well too bad - doing it anyway ;)'

            mm.get(src)[messageKey] = {'name': self.functionNiceName, 'fn': self.functionToMap}

            import midimaps
            midimaps.MidiMapping().saveMaps(mm)

            self.cancel()  # Go back


        except:
            print 'failed for some reason'
            pass

    def cancel(self):
        # print devices
        gv.displayer.disp_change('-' * 20, line=2, timeout=0)
        gv.learningMode = False
        if len(self.menuCoords) > 1:
            self.menuCoords.pop()
            self.loadState(MenuNav)
        else:
            self.loadState(MenuNav)  # this will become the gv.presets state


# ______________________________________________________________________________

class DeleteMidiMap(Navigator):
    def __init__(self, functionToUnmap, functionNiceName):

        self.midimaps = gv.midimaps
        # src[:src.rfind(" "):] # use this to strip the port number off the end of src

        self.functionToUnmap = functionToUnmap
        self.functionNiceName = functionNiceName

        matchedMappings = {}
        i = 0
        for devices in self.midimaps.iteritems():
            deviceName = devices[0]
            deviceMaps = devices[1]
            for midiKey, midiKeyDict in deviceMaps.iteritems():
                # print mm2
                for midiKeyItem in midiKeyDict.iteritems():
                    fnName = midiKeyItem[1]
                    if fnName == functionToUnmap:
                        # Build a new dictionary to build dict addresses for matched keys

                        matchedMappings[i] = [deviceName, midiKey, functionToUnmap]
                        i += 1

        self.matchedMappings = matchedMappings
        self.i = 0

        self.deleteDisplay()

    def deleteDisplay(self):
        mm = self.matchedMappings
        functionNiceName = self.functionNiceName
        i = self.i
        # lcd.display(mm[i][2], 1)
        gv.displayer.disp_change(str(i + 1) + ' ' + functionNiceName, line=1, timeout=0)
        gv.displayer.disp_change(str(mm[i][0])[:8] + str(mm[i][1][:8]), line=2, timeout=0)

    def left(self):
        if self.i > 0:
            self.i -= 1
            self.deleteDisplay()

    def right(self):
        if self.i < len(self.matchedMappings) - 1:
            self.i += 1
            self.deleteDisplay()

    def enter(self):
        a = {}

        mm = self.midimaps
        deviceName = self.matchedMappings[self.i][0]
        midiKey = self.matchedMappings[self.i][1]
        functionToUnmap = self.matchedMappings[self.i][2]
        try:

            for device in mm.iteritems():
                if deviceName in device:
                    device[1].pop(midiKey)

            import midimaps
            midimaps.MidiMapping().saveMaps(mm)

            self.cancel()  # Go back


        except:
            print 'failed for some reason'
            pass

    def cancel(self):
        # print devices
        gv.displayer.disp_change('=' * 20, line=2, timeout=0)

        gv.learningMode = False
        if len(self.menuCoords) > 1:
            self.menuCoords.pop()
            self.loadState(MenuNav)
        else:
            self.loadState(MenuNav)  # this will become the gv.presets state


# ______________________________________________________________________________


class MaxPolyphonyConfig(Navigator):
    def __init__(self):
        self.MAX_POLYPHONY = gv.MAX_POLYPHONY
        self.display()

    def display(self):
        gv.displayer.disp_change('Max polyphony', line=1, timeout=0)
        gv.displayer.disp_change(str(self.MAX_POLYPHONY) + ' (1-128)', line=2, timeout=0)

    def left(self):
        self.MAX_POLYPHONY = max(self.MAX_POLYPHONY - 1, 1)
        self.display()

    def right(self):
        self.MAX_POLYPHONY = min(self.MAX_POLYPHONY + 1, 128)
        self.display()

    def enter(self):
        cs.update_config('SAMPLERBOX CONFIG', 'MAX_POLYPHONY', str(self.MAX_POLYPHONY))
        gv.MAX_POLYPHONY = self.MAX_POLYPHONY
        print '-- requires a restart --'  # or a reinstantiation of the sounddevice
        self.loadState(MenuNav)

    def cancel(self):
        self.loadState(MenuNav)


# ______________________________________________________________________________

class MidiChannelConfig(Navigator):
    def __init__(self):
        print '-= MIDI Channel !IMPORTANT: All MIDI ports are open with rtmidi2 =-'
        self.MIDI_CHANNEL = gv.MIDI_CHANNEL
        self.display()

    def display(self):
        gv.displayer.disp_change('MIDI Channel', line=1, timeout=0)
        gv.displayer.disp_change(str(self.MIDI_CHANNEL) + ' (1-128)', line=2, timeout=0)

    def left(self):
        self.MIDI_CHANNEL = max(self.MIDI_CHANNEL - 1, 1)
        print self.MIDI_CHANNEL

    def right(self):
        self.MIDI_CHANNEL = min(self.MIDI_CHANNEL + 1, 16)
        print self.MIDI_CHANNEL

    def enter(self):
        cs.update_config('SAMPLERBOX CONFIG', 'MIDI_CHANNEL', str(self.MIDI_CHANNEL))
        gv.MIDI_CHANNEL = self.MIDI_CHANNEL
        print '-- requires a restart (maybe?) --'  # or a reinstantiation of the audio device
        self.loadState(MenuNav)

    def cancel(self):
        self.loadState(MenuNav)


# ______________________________________________________________________________

class ChannelsConfig(Navigator):
    def __init__(self):
        self.CHANNELS = gv.CHANNELS
        self.options = [1, 2, 4, 6, 8]
        self.i = 1
        for x in self.options:
            if x == self.CHANNELS:
                self.i = self.options.index(x)
        self.display()

    def display(self):
        gv.displayer.disp_change('Audio Channels', line=1, timeout=0)
        gv.displayer.disp_change('[' + str(self.CHANNELS) + ']' + ' (1,2,4,6,8)', line=2, timeout=0)

    def left(self):
        if self.i > 0:
            self.i -= 1
        self.CHANNELS = max(self.options[self.i], self.options[0])
        self.display()

    def right(self):
        if self.i < len(self.options) - 1:
            self.i += 1
        self.CHANNELS = min(self.options[self.i], self.options[-1])
        self.display()

    def enter(self):
        cs.update_config('SAMPLERBOX CONFIG', 'CHANNELS', str(self.CHANNELS))
        gv.CHANNELS = self.CHANNELS
        print '-- requires a restart (maybe?) --'  # or a reinstantiation of the sounddevice
        self.loadState(MenuNav)

    def cancel(self):
        self.loadState(MenuNav)


# ______________________________________________________________________________

class BufferSizeConfig(Navigator):
    def __init__(self):
        self.BUFFERSIZE = gv.BUFFERSIZE
        self.options = [16, 32, 64, 128, 256, 512, 1024, 2048]
        self.i = 3
        for x in self.options:
            if x == self.BUFFERSIZE:
                self.i = self.options.index(x)
        self.display()

    def display(self):
        gv.displayer.disp_change('Buffer size', line=1, timeout=0)
        gv.displayer.disp_change(str(self.BUFFERSIZE), line=2, timeout=0)

    def left(self):
        if self.i > 0:
            self.i -= 1
        self.BUFFERSIZE = max(self.options[self.i], self.options[0])
        self.display()

    def right(self):
        if self.i < len(self.options) - 1:
            self.i += 1
        self.BUFFERSIZE = min(self.options[self.i], self.options[-1])
        self.display()

    def enter(self):
        cs.update_config('SAMPLERBOX CONFIG', 'BUFFERSIZE', str(self.BUFFERSIZE))
        gv.BUFFERSIZE = self.BUFFERSIZE
        print '-- requires a restart (maybe?) --'  # or a reinstantiation of the sounddevice
        self.loadState(MenuNav)

    def cancel(self):
        self.loadState(MenuNav)


# ______________________________________________________________________________

class SampleRateConfig(Navigator):
    def __init__(self):
        self.SAMPLERATE = gv.SAMPLERATE
        self.options = [44100, 48000, 96000]
        self.i = 0
        for x in self.options:
            if x == self.SAMPLERATE:
                self.i = self.options.index(x)
        self.display()

    def display(self):
        gv.displayer.disp_change('Sample rate', line=1, timeout=0)
        gv.displayer.disp_change(str(self.SAMPLERATE), line=2, timeout=0)

    def left(self):
        if self.i > 0:
            self.i -= 1
        self.SAMPLERATE = max(self.options[self.i], self.options[0])
        self.display()

    def right(self):
        if self.i < len(self.options) - 1:
            self.i += 1
        self.SAMPLERATE = min(self.options[self.i], self.options[-1])
        self.display()

    def enter(self):
        cs.update_config('SAMPLERBOX CONFIG', 'SAMPLERATE', str(self.SAMPLERATE))
        gv.SAMPLERATE = self.SAMPLERATE
        print '-- requires a restart (maybe?) --'  # or a reinstantiation of the sounddevice
        self.loadState(MenuNav)

    def cancel(self):
        self.loadState(MenuNav)


# ______________________________________________________________________________

import midicallback


class MasterVolumeConfig(Navigator):
    def __init__(self):
        self.display()

    def display(self):
        gv.displayer.disp_change('Master volume', line=1, timeout=0)
        gv.displayer.disp_change(str(gv.global_volume), line=2, timeout=0)

    def left(self):
        gv.global_volume = max(gv.global_volume - 4, 0)
        midicallback.MasterVolume().setvolume(gv.global_volume * 1.27)
        self.display()

    def right(self):
        gv.global_volume = min(gv.global_volume + 4, 100)
        midicallback.MasterVolume().setvolume(gv.global_volume * 1.27)
        self.display()

    def enter(self):
        cs.update_config('SAMPLERBOX CONFIG', 'GLOBAL_VOLUME', str(gv.global_volume))
        self.loadState(MenuNav)

    def cancel(self):
        self.enter()


# _____________________________________________________________________________

from modules import definitionparser


def set_global_from_keyword(keyword, value):
    keyword = keyword.strip('%%')
    if isinstance(value, str): value = value.title()
    for gvar, k in definitionparser.keywords_to_try:
        if k == keyword:
            if 'release' in keyword: value = value * 10000
            print '>>>>>>>Setting global from keyword. %s: %s' % (keyword, str(value))  # debug
            exec (gvar + '=value')  # set the global variable


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


class EditDefinition(Navigator):
    def __init__(self):

        self.in_a_mode = False
        self.mode = 0
        self.selected_keyword = None
        self.allowed_values = None
        self.i = 0
        self.selected_keyword_value = None

        self.setlist_list = open(gv.SETLIST_FILE_PATH).read().splitlines()
        self.prev_state = SelectSong
        self.song_name = self.setlist_list[int(gv.preset)]
        self.dp = definitionparser.DefinitionParser(self.song_name)
        self.keywords_dict = self.dp.keywords_dict
        self.keywords_defaults_dict = self.dp.keywords_defaults_dict
        self.display()

    def display(self):
        if not self.in_a_mode:
            keyword_str = self.keywords_dict[self.mode].items()[0][0].strip('%%').title()
            gv.displayer.disp_change(self.song_name, line=1, timeout=0)
            gv.displayer.disp_change(keyword_str, line=2, timeout=0)
        else:
            keyword = self.keywords_dict[self.mode].items()[0][0]
            keyword_str = keyword.strip('%%').title()
            if isinstance(self.allowed_values, list):
                value_str = str(self.allowed_values[self.i])
            elif isinstance(self.allowed_values, tuple):
                value_str = str(self.i)
            line_str = keyword_str + ' ' + value_str
            gv.displayer.disp_change(self.song_name, line=1, timeout=0)
            gv.displayer.disp_change(line_str, line=2, timeout=0)

    def left(self):
        if not self.in_a_mode:
            if not self.mode <= 0:
                self.mode -= 1
        else:
            if isinstance(self.allowed_values, list):
                if not self.i <= 0:
                    self.i -= 1
                    self.selected_keyword_value = self.allowed_values[self.i]
            elif isinstance(self.allowed_values, tuple):
                self.i = clamp(int(self.i) - 1, self.allowed_values[0], self.allowed_values[1])
                self.selected_keyword_value = self.i

            set_global_from_keyword(self.selected_keyword, self.selected_keyword_value)

        self.display()

    def right(self):
        if not self.in_a_mode:
            if not self.mode >= len(self.keywords_dict) - 1:
                self.mode += 1
        else:
            if isinstance(self.allowed_values, list):
                if not self.i >= len(self.allowed_values) - 1:
                    self.i += 1
                    self.selected_keyword_value = self.allowed_values[self.i]
            elif isinstance(self.allowed_values, tuple):
                self.i = clamp(int(self.i) + 1, self.allowed_values[0], self.allowed_values[1])
                self.selected_keyword_value = self.i

            set_global_from_keyword(self.selected_keyword, self.selected_keyword_value)

        self.display()

    def enter(self):
        if not self.in_a_mode:
            self.in_a_mode = True
            self.selected_keyword = self.keywords_dict[self.mode].items()[0][0]
            self.allowed_values = self.keywords_dict[self.mode].items()[0][1]
            if self.dp.existing_patterns.has_key(self.selected_keyword):

                self.selected_keyword_value = self.dp.existing_patterns[self.selected_keyword]
                if isinstance(self.allowed_values, list):
                    self.i = self.allowed_values.index(self.selected_keyword_value)
                elif isinstance(self.allowed_values, tuple):
                    self.i = self.selected_keyword_value

                print '### %s exists with a value of %s ###' \
                      % (self.selected_keyword.title(), str(self.selected_keyword_value).title())
            else:
                self.i = int(self.keywords_defaults_dict[self.selected_keyword])
                if isinstance(self.allowed_values, list):
                    self.selected_keyword_value = self.keywords_dict[self.i]
                elif isinstance(self.allowed_values, tuple):
                    self.selected_keyword_value = self.i
                print '### %s does not exist. Set default: %d ###' \
                      % (self.selected_keyword.title(), self.i)
            self.display()
        elif self.in_a_mode:

            if isinstance(self.allowed_values, list):
                self.dp.set_new_keyword(self.selected_keyword, str(self.selected_keyword_value))
            elif isinstance(self.allowed_values, tuple):
                self.dp.set_new_keyword(self.selected_keyword, int(self.selected_keyword_value))

            self.dp.compare_existing_patterns()
            self.dp.write_definition_file()

            self.loadState(EditDefinition)

    def cancel(self):
        if not self.in_a_mode:
            Navigator.state = self.prev_state(EditDefinition)
        elif self.in_a_mode:
            self.in_a_mode = False
            self.display()


class AudioDevice(Navigator):

    def __init__(self):
        import sound
        self.all_audio_devices = sound.get_all_audio_devices()
        self.i = 0
        self.device_name = str(self.all_audio_devices[self.i].get('name'))
        self.display(False)

    def display(self, changed=False):
        gv.displayer.disp_change('Choose new audio device', line=1, timeout=0)
        if changed:
            gv.displayer.disp_change('Device changed', line=2, timeout=0)
            gv.displayer.disp_change(self.device_name, line=3, timeout=0)
        else:
            gv.displayer.disp_change(self.device_name, line=2, timeout=0)
            gv.displayer.disp_change('', line=3, timeout=0)

    def left(self):
        if self.i > 0:
            self.i -= 1
        self.device_name = str(self.all_audio_devices[self.i].get('name'))
        self.display(False)

    def right(self):
        if self.i < len(self.all_audio_devices) - 1:
            self.i += 1
        self.device_name = str(self.all_audio_devices[self.i].get('name'))
        self.display(False)

    def enter(self):
        import sound
        sound.set_audio_device(self.device_name)
        self.display(changed=True)

    def cancel(self):
        self.loadState(MenuNav)