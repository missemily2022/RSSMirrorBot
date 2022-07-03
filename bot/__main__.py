import shutil, psutil
import signal
import os
import asyncio
import time
import subprocess

from pyrogram import idle, filters, types, emoji

from bot import app, alive
from sys import executable
from datetime import datetime
import pytz
import time
import threading

from telegram.error import BadRequest, Unauthorized
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext, InlineQueryHandler

from wserver import start_server_async
from bot import bot, app, dispatcher, updater, botStartTime, IGNORE_PENDING_REQUESTS, IS_VPS, PORT, alive, web, OWNER_ID, AUTHORIZED_CHATS, LOGGER, TIMEZONE, RESTARTED_GROUP_ID
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendLogFile
from .helper.ext_utils.telegraph_helper import telegraph
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper import button_build
from .modules import authorize, list, cancel_mirror, mirror_status, mirror, clone, watch, shell, eval, delete, speedtest, count, leech_settings, search, imdb, mediainfo

now=datetime.now(pytz.timezone(f'{TIMEZONE}'))

def stats(update, context):
    currentTime = get_readable_time(time.time() - botStartTime)
    current = now.strftime('%m/%d %I:%M:%S %p')
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>•• ━━ Emily RSS Bot ━━ ••</b>\n\n' \
            f'Rᴜɴɴɪɴɢ Sɪɴᴄᴇ : {currentTime}\n' \
            f'Sᴛᴀʀᴛᴇᴅ Aᴛ : {current}\n\n' \
            f'<b>DISK INFO</b>\n' \
            f'<b><i>Total</i></b>: {total}\n' \
            f'<b><i>Used</i></b>: {used} ~ ' \
            f'<b><i>Free</i></b>: {free}\n\n' \
            f'<b>DATA USAGE</b>\n' \
            f'<b><i>UL</i></b>: {sent} ~ ' \
            f'<b><i>DL</i></b>: {recv}\n\n' \
            f'<b>SERVER STATS</b>\n' \
            f'<b><i>CPU</i></b>: {cpuUsage}%\n' \
            f'<b><i>RAM</i></b>: {memory}%\n' \
            f'<b><i>DISK</i></b>: {disk}%\n' \
            f'<b>•• ━ ɱαԃҽ ɯιƚԋ ʅσʋҽ Ⴆყ Miss Emily ━ ••</b>\n\n'
    sendMessage(stats, context.bot, update)


def call_back_data(update, context):
    global main
    query = update.callback_query
    query.answer()
    main.delete()
    main = None


def start(update, context):
    LOGGER.info(
        f'UID: {update.message.chat.id} - UN: {update.message.chat.username} - MSG: {update.message.text}'
    )

    uptime = get_readable_time((time.time() - botStartTime))
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        if update.message.chat.type == "private" :
            reply_message = sendMessage(f"<b>🤗Hello {update.message.chat.first_name}</b>,\n\nWelcome to Emily Mirror Mirror Bot", context.bot, update)
            threading.Thread(target=auto_delete_message, args=(bot, update.message, reply_message)).start()
        else :
            sendMessage(f"<b>I'm Awake Already!</b>\n<b>Haven't Slept Since:</b> <code>{uptime}</code>", context.bot, update)
    else :
        uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
        sendMessage(f"<b>Hi {uname},</b>\n\n<b>If You Want To Use Me</b>\n\n<b>You Have To Join Emily Mirror</b>", context.bot, update)
        
def restart(update, context):
    restart_message = sendMessage("Restarting...", context.bot, update)
    fs_utils.clean_all()
    alive.kill()
    process = psutil.Process(web.pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()
    subprocess.run(["python3", "update.py"])
    # Save restart message object in order to reply to it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    os.execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update)


help_string_telegraph = f'''<br>
<b>/{BotCommands.HelpCommand}</b>: To get this message
<br><br>
<b>/{BotCommands.MirrorCommand}</b> [download_url][magnet_link]: Start mirroring to Google Drive. Send <b>/{BotCommands.MirrorCommand}</b> for more help
<br><br>
<b>/{BotCommands.ZipMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the file/folder compressed with zip extension
<br><br>
<b>/{BotCommands.UnzipMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the file/folder extracted from any archive extension
<br><br>
<b>/{BotCommands.QbMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start Mirroring using qBittorrent, Use <b>/{BotCommands.QbMirrorCommand} s</b> to select files before downloading
<br><br>
<b>/{BotCommands.QbZipMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start mirroring using qBittorrent and upload the file/folder compressed with zip extension
<br><br>
<b>/{BotCommands.QbUnzipMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start mirroring using qBittorrent and upload the file/folder extracted from any archive extension
<br><br>
<b>/{BotCommands.LeechCommand}</b> [download_url][magnet_link]: Start leeching to Telegram, Use <b>/{BotCommands.LeechCommand} s</b> to select files before leeching
<br><br>
<b>/{BotCommands.ZipLeechCommand}</b> [download_url][magnet_link]: Start leeching to Telegram and upload the file/folder compressed with zip extension
<br><br>
<b>/{BotCommands.UnzipLeechCommand}</b> [download_url][magnet_link][torent_file]: Start leeching to Telegram and upload the file/folder extracted from any archive extension
<br><br>
<b>/{BotCommands.QbLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent, Use <b>/{BotCommands.QbLeechCommand} s</b> to select files before leeching
<br><br>
<b>/{BotCommands.QbZipLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent and upload the file/folder compressed with zip extension
<br><br>
<b>/{BotCommands.QbUnzipLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent and upload the file/folder extracted from any archive extension
<br><br>
<b>/{BotCommands.CloneCommand}</b> [drive_url][gdtot_url]: Copy file/folder to Google Drive
<br><br>
<b>/{BotCommands.CountCommand}</b> [drive_url][gdtot_url]: Count file/folder of Google Drive
<br><br>
<b>/{BotCommands.DeleteCommand}</b> [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo)
<br><br>
<b>/{BotCommands.WatchCommand}</b> [yt-dlp supported link]: Mirror yt-dlp supported link. Send <b>/{BotCommands.WatchCommand}</b> for more help
<br><br>
<b>/{BotCommands.ZipWatchCommand}</b> [yt-dlp supported link]: Mirror yt-dlp supported link as zip
<br><br>
<b>/{BotCommands.LeechWatchCommand}</b> [yt-dlp supported link]: Leech yt-dlp supported link
<br><br>
<b>/{BotCommands.LeechZipWatchCommand}</b> [yt-dlp supported link]: Leech yt-dlp supported link as zip
<br><br>
<b>/{BotCommands.LeechSetCommand}</b>: Leech settings
<br><br>
<b>/{BotCommands.SetThumbCommand}</b>: Reply photo to set it as Thumbnail
<br><br>
<b>/{BotCommands.CancelMirror}</b>: Reply to the message by which the download was initiated and that download will be cancelled
<br><br>
<b>/{BotCommands.CancelAllCommand}</b>: Cancel all downloading tasks
<br><br>
<b>/{BotCommands.ListCommand}</b> [query]: Search in Google Drive(s)
<br><br>
<b>/{BotCommands.SearchCommand}</b> [query]: Search for torrents with API
<br>sites: <code>rarbg, 1337x, yts, etzv, tgx, torlock, piratebay, nyaasi, ettv</code><br><br>
<b>/{BotCommands.StatusCommand}</b>: Shows a status of all the downloads
<br><br>
<b>/{BotCommands.StatsCommand}</b>: Show Stats of the machine the bot is hosted on
'''

help = telegraph.create_page(
        title='Emily-Mirror Help',
        content=help_string_telegraph,
    )["path"]

help_string = f'''
/{BotCommands.PingCommand}: Check how long it takes to Ping the Bot

/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)

/{BotCommands.UnAuthorizeCommand}: Unauthorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)

/{BotCommands.AuthorizedUsersCommand}: Show authorized users (Only Owner & Sudo)

/{BotCommands.AddSudoCommand}: Add sudo user (Only Owner)

/{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner)

/{BotCommands.RestartCommand}: Restart and update the bot

/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports

/{BotCommands.SpeedCommand}: Check Internet Speed of the Host

/{BotCommands.ShellCommand}: Run commands in Shell (Only Owner)

/{BotCommands.ExecHelpCommand}: Get help for Executor module (Only Owner)

/{BotCommands.MediainfoHelpCommand}: Get detailed info about the replied media

/{BotCommands.ImdbHelpCommand}: get IMDB information.
'''


def bot_help(update, context):
    button = button_build.ButtonMaker()
    button.buildbutton("Other Commands", f"https://telegra.ph/{help}")
    reply_markup = InlineKeyboardMarkup(button.build_menu(1))
    sendMarkup(help_string, context.bot, update, reply_markup)
  
botcmds = [

        (f'{BotCommands.MirrorCommand}', 'Mirror using Aria2'),
        (f'{BotCommands.ZipMirrorCommand}','Mirror and upload as zip'),
        (f'{BotCommands.UnzipMirrorCommand}','Mirror and extract files'),
        (f'{BotCommands.QbMirrorCommand}','Mirror torrent using qBittorrent'),
        (f'{BotCommands.QbZipMirrorCommand}','Mirror torrent and upload as zip using qb'),
        (f'{BotCommands.QbUnzipMirrorCommand}','Mirror torrent and extract files using qb'),
        (f'{BotCommands.StatusCommand}','Get mirror status message'),
        (f'{BotCommands.StatsCommand}','Bot usage stats'),
    ]


def main():     
    GROUP_ID = f'{RESTARTED_GROUP_ID}'
    kie = datetime.now(pytz.timezone(f'{TIMEZONE}'))
    jam = kie.strftime('\n 𝐃𝐚𝐭𝐞: %d/%m/%Y\n 𝐃𝐚𝐭𝐞: %I:%M%P\n 𝐓𝐢𝐦𝐞𝐙𝐨𝐧𝐞: Asia/Kolkata')
    if GROUP_ID is not None and isinstance(GROUP_ID, str):        
        try:
            dispatcher.bot.sendMessage(f"{GROUP_ID}", f" 𝐌𝐢𝐫𝐫𝐨𝐫 𝐁𝐨𝐭 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐑𝐞𝐛𝐨𝐨𝐭𝐞𝐝 ! \n{jam}\n\nℹ️ 𝐘𝐨𝐮 𝐰𝐢𝐥𝐥 𝐧𝐞𝐞𝐝 𝐭𝐨 𝐚𝐠𝐚𝐢𝐧 𝐒𝐭𝐚𝐫𝐭 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐬 𝐧𝐨𝐰 !!! \n\nCourtesy of 𝐄𝐦𝐢𝐥𝐲 𝐌𝐢𝐫𝐫𝐨𝐫 \n#Rebooted")
        except Unauthorized:
            LOGGER.warning(
                "Bot is not able to send Restart Message to Group ID !"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)
            
    fs_utils.start_cleanup()
    if IS_VPS:
        asyncio.get_event_loop().run_until_complete(start_server_async(PORT))
    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("𝚁𝚎𝚜𝚝𝚊𝚛𝚝𝚎𝚍 𝚜𝚞𝚌𝚌𝚎𝚜𝚜𝚏𝚞𝚕𝚕𝚢!", chat_id, msg_id)
        os.remove(".restartmsg")
    elif OWNER_ID:
        try:
            kie = datetime.now(pytz.timezone(f'{TIMEZONE}'))
            jam = kie.strftime('\n 𝐃𝐚𝐭𝐞: %d/%m/%Y\n 𝐃𝐚𝐭𝐞: %I:%M%P\n 𝐓𝐢𝐦𝐞𝐙𝐨𝐧𝐞: Asia/Kolkata')
            text = f" 𝐌𝐢𝐫𝐫𝐨𝐫 𝐁𝐨𝐭 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐑𝐞𝐛𝐨𝐨𝐭𝐞𝐝 ! \n{jam}\n\nℹ️ 𝐘𝐨𝐮 𝐰𝐢𝐥𝐥 𝐧𝐞𝐞𝐝 𝐭𝐨 𝐚𝐠𝐚𝐢𝐧 𝐒𝐭𝐚𝐫𝐭 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐬 𝐧𝐨𝐰 !!! \n\nCourtesy of 𝐄𝐦𝐢𝐥𝐲 𝐌𝐢𝐫𝐫𝐨𝐫 \n#Rebooted"
            bot.sendMessage(chat_id=OWNER_ID, text=text, parse_mode=ParseMode.HTML)
            if AUTHORIZED_CHATS:
                for i in AUTHORIZED_CHATS:
                    bot.sendMessage(chat_id=i, text=text, parse_mode=ParseMode.HTML)
        except Exception as e:
            LOGGER.warning(e)

    bot.set_my_commands(botcmds)        
    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    del_data_msg = CallbackQueryHandler(call_back_data, pattern="stats_close")
    
    dispatcher.add_handler(del_data_msg)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)

app.start()
main()
idle()
