import discord
from discord.ext import commands
import os
from yt_dlp import YoutubeDL
import logging
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger('bot')

class YouTubeDownloader(commands.Cog):
    """Module de téléchargement YouTube"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color(0x2BA3B3)
        self.icon_url = "https://i.imgur.com/YSQ8PBN.png"
        logger.info("📥 Module YouTube Downloader chargé")

    def get_ydl_opts(self, type: str = "audio") -> dict:
        """Retourne les options yt-dlp selon le type"""
        base_opts = {
            'extract_flat': True,
            'get_url': True,
            'quiet': True,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr,fr-FR;q=0.9,en;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            }
        }
        
        if type == "audio":
            return {
                **base_opts,
                'format': 'bestaudio[ext=mp3]/bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'prefer_insecure': True,
                'geo_bypass': True,
                'geo_bypass_country': 'FR'
            }
        return {
            **base_opts,
            'format': 'best[ext=mp4]/best',
            'prefer_insecure': True,
            'geo_bypass': True,
            'geo_bypass_country': 'FR'
        }

    async def extract_info(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extrait les informations de la vidéo"""
        try:
            # Extraction audio
            with YoutubeDL(self.get_ydl_opts("audio")) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info.get('url')
                title = info.get('title', 'Audio')
                thumbnail = info.get('thumbnail')
            
            # Extraction vidéo
            with YoutubeDL(self.get_ydl_opts("video")) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
            
            return audio_url, video_url, title, thumbnail
        except Exception as e:
            logger.error(f"Erreur d'extraction: {e}")
            return None, None, None, None

    def create_info_embed(self, title: str, thumbnail: str, author: discord.Member) -> discord.Embed:
        """Crée l'embed d'information"""
        embed = discord.Embed(
            title=f"📽️ {title[:200]}{'...' if len(title) > 200 else ''}",
            color=self.color,
            timestamp=discord.utils.utcnow()
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        
        embed.add_field(
            name="ℹ️ Détails",
            value=f"```yml\n"
                  f"Extrait le : {discord.utils.format_dt(discord.utils.utcnow(), 'R')}\n"
                  f"Par        : {author.display_name}```",
            inline=False
        )
        embed.set_footer(text="MathysieBot™ • Informations", icon_url=self.icon_url)
        return embed

    def create_links_embed(self, audio_url: str, video_url: str) -> discord.Embed:
        """Crée l'embed des liens"""
        embed = discord.Embed(
            title="📥 Liens de téléchargement",
            color=self.color,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="🎵 Format Audio",
            value=f"[Télécharger MP3]({audio_url})\n`Meilleure qualité`",
            inline=True
        )
        embed.add_field(
            name="🎬 Format Vidéo",
            value=f"[Télécharger MP4]({video_url})\n`Résolution maximale`",
            inline=True
        )
        embed.set_footer(text="MathysieBot™ • YouTube Extractor", icon_url=self.icon_url)
        return embed

    def create_audio_embed(self, title: str, audio_url: str, thumbnail: str, author: discord.Member) -> discord.Embed:
        """Crée l'embed audio"""
        embed = discord.Embed(
            title=f"🎵 Format Audio - {title[:100]}{'...' if len(title) > 100 else ''}",
            description=f"[Télécharger MP3]({audio_url})",  # URL complète dans la description
            color=self.color,
            timestamp=discord.utils.utcnow()
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        
        embed.add_field(
            name="📥 Format",
            value="`MP3 - Meilleure qualité`",
            inline=True
        )
        
        embed.add_field(
            name="ℹ️ Détails",
            value=f"```yml\nExtrait le : {discord.utils.format_dt(discord.utils.utcnow(), 'R')}\n"
                  f"Par        : {author.display_name}```",
            inline=False
        )
        embed.set_footer(text="MathysieBot™ • YtDw", icon_url=self.icon_url)
        return embed

    def create_video_embed(self, title: str, video_url: str, thumbnail: str, author: discord.Member) -> discord.Embed:
        """Crée l'embed vidéo"""
        embed = discord.Embed(
            title=f"🎬 Format Vidéo - {title[:100]}{'...' if len(title) > 100 else ''}",
            description=f"[Télécharger MP4]({video_url})",  # URL complète dans la description
            color=self.color,
            timestamp=discord.utils.utcnow()
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        
        embed.add_field(
            name="📥 Format",
            value="`MP4 - Résolution maximale`",
            inline=True
        )
        
        embed.add_field(
            name="ℹ️ Détails",
            value=f"```yml\nExtrait le : {discord.utils.format_dt(discord.utils.utcnow(), 'R')}\n"
                  f"Par        : {author.display_name}```",
            inline=False
        )
        embed.set_footer(text="MathysieBot™ • YtDw", icon_url=self.icon_url)
        return embed

    @commands.command(
        name="ytdw",
        help="Télécharge une vidéo YouTube",
        description="Extrait les liens audio et vidéo d'une URL YouTube",
        usage="!ytdw <url>"
    )
    async def download(self, ctx: commands.Context, url: str):
        """Télécharge le contenu d'une URL YouTube"""
        loading_msg = await ctx.send("🔄 Extraction des liens en cours...")

        try:
            audio_url, video_url, title, thumbnail = await self.extract_info(url)
            
            if all([audio_url, video_url, title]):
                audio_embed = self.create_audio_embed(title, audio_url, thumbnail, ctx.author)
                video_embed = self.create_video_embed(title, video_url, thumbnail, ctx.author)
                
                await loading_msg.edit(content=None, embed=audio_embed)
                await ctx.send(embed=video_embed)
            else:
                await loading_msg.edit(content="❌ Impossible d'extraire les liens.")
                
        except Exception as e:
            logger.error(f"Erreur YouTube Downloader: {str(e)}")
            await loading_msg.edit(content=f"❌ Erreur lors de l'extraction : {str(e)}")

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
    logger.info("✅ YouTube Downloader cog loaded")