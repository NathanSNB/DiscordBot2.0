import discord
from discord.ext import commands
import logging
from .database import db_manager

logger = logging.getLogger('bot')

class AccessManager:
    """Gestionnaire des whitelist/blacklist pour les serveurs (utilise la DB globale)"""
    
    @staticmethod
    async def check_guild_access(guild: discord.Guild) -> bool:
        """Vérifie si un serveur est autorisé"""
        return await db_manager.is_guild_allowed(guild.id)
    
    @staticmethod
    async def add_guild_to_whitelist(guild_id: int, reason: str = None, added_by: int = None):
        """Ajoute un serveur à la whitelist"""
        await db_manager.add_to_access_list(guild_id, 'whitelist', reason, added_by)
        logger.info(f"✅ Serveur {guild_id} ajouté à la whitelist")
    
    @staticmethod
    async def add_guild_to_blacklist(guild_id: int, reason: str = None, added_by: int = None):
        """Ajoute un serveur à la blacklist"""
        await db_manager.add_to_access_list(guild_id, 'blacklist', reason, added_by)
        logger.info(f"🚫 Serveur {guild_id} ajouté à la blacklist")
    
    @staticmethod
    async def remove_guild_from_whitelist(guild_id: int):
        """Retire un serveur de la whitelist"""
        await db_manager.remove_from_access_list(guild_id, 'whitelist')
        logger.info(f"❌ Serveur {guild_id} retiré de la whitelist")
    
    @staticmethod
    async def remove_guild_from_blacklist(guild_id: int):
        """Retire un serveur de la blacklist"""
        await db_manager.remove_from_access_list(guild_id, 'blacklist')
        logger.info(f"✅ Serveur {guild_id} retiré de la blacklist")

class AccessControlCog(commands.Cog):
    """Commandes de gestion des accès (pour les propriétaires du bot)"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="whitelist")
    @commands.is_owner()
    async def whitelist_guild(self, ctx, guild_id: int, *, reason: str = None):
        """Ajoute un serveur à la whitelist"""
        await AccessManager.add_guild_to_whitelist(guild_id, reason, ctx.author.id)
        await ctx.send(f"✅ Serveur `{guild_id}` ajouté à la whitelist")
    
    @commands.command(name="blacklist")
    @commands.is_owner()
    async def blacklist_guild(self, ctx, guild_id: int, *, reason: str = None):
        """Ajoute un serveur à la blacklist"""
        await AccessManager.add_guild_to_blacklist(guild_id, reason, ctx.author.id)
        
        # Quitter le serveur s'il est connecté
        guild = self.bot.get_guild(guild_id)
        if guild:
            try:
                await guild.leave()
                await ctx.send(f"🚫 Serveur `{guild_id}` ({guild.name}) ajouté à la blacklist et quitté")
            except:
                await ctx.send(f"🚫 Serveur `{guild_id}` ajouté à la blacklist mais impossible de le quitter")
        else:
            await ctx.send(f"🚫 Serveur `{guild_id}` ajouté à la blacklist")
    
    @commands.command(name="unwhitelist")
    @commands.is_owner()
    async def unwhitelist_guild(self, ctx, guild_id: int):
        """Retire un serveur de la whitelist"""
        await AccessManager.remove_guild_from_whitelist(guild_id)
        await ctx.send(f"❌ Serveur `{guild_id}` retiré de la whitelist")
    
    @commands.command(name="unblacklist")
    @commands.is_owner()
    async def unblacklist_guild(self, ctx, guild_id: int):
        """Retire un serveur de la blacklist"""
        await AccessManager.remove_guild_from_blacklist(guild_id)
        await ctx.send(f"✅ Serveur `{guild_id}` retiré de la blacklist")

async def setup(bot):
    await bot.add_cog(AccessControlCog(bot))
