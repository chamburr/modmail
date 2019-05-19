import sys
import traceback
import datetime
import discord
import sqlite3
from discord.ext import commands

import config
import utils

conn = sqlite3.connect('data.sqlite')


class ModMail(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = datetime.datetime.utcnow()

    @property
    def conn(self):
        return conn

    @property
    def uptime(self):
        return datetime.datetime.utcnow() - self.start_time

    @property
    def version(self):
        return config.__version__

    @property
    def config(self):
        return config

    @property
    def primary_colour(self):
        return config.primary_colour

    @property
    def user_colour(self):
        return config.user_colour

    @property
    def mod_colour(self):
        return config.mod_colour

    @property
    def error_colour(self):
        return config.error_colour

    @property
    def utils(self):
        return utils

    def get_data(self, guild):
        c = self.conn.cursor()
        c.execute("SELECT * FROM data WHERE guild=?", (guild,))
        res = c.fetchone()
        if not res:
            c.execute("INSERT INTO data VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (guild, None, None, None, None, None, None, None))
            self.conn.commit()
            return self.get_data(guild)
        else:
            return res

    all_prefix = {}
    all_category = []

    async def start_bot(self):
        c = self.conn.cursor()
        c.execute("SELECT guild, prefix, category FROM data")
        res = c.fetchall()
        for row in res:
            self.all_prefix[row[0]] = row[1]
            if row[2] is not None:
                self.all_category.append(row[2])
        for extension in self.config.initial_extensions:
            try:
                self.load_extension(extension)
            except Exception:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()
        await self.start(self.config.token)
