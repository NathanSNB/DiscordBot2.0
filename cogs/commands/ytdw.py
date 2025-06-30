import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
import re
from datetime import timedelta
import logging
from typing import Optional, Tuple
from datetime import datetime

from utils.embed_manager import EmbedManager

logger = logging.getLogger('bot')

# Constants à ajouter en haut du fichier
EMOJIS = {
    'error': '❌',
    'youtube': '📺',
    'channel': '📢',
    'views': '👁️',
    'date': '📅',
    'duration': '⏱️',
    'link': '🔗',
    'download': '📥',
    'progress': '▰',  # Caractère pour la barre de progression
    'empty': '▱',     # Caractère vide pour la barre de progression
    'warning': '⚠️',
    'info': 'ℹ️'
}

COLORS = {
    'error': discord.Color.red(),
    'info': discord.Color.blurple(),
    'primary': discord.Color(0x2BA3B3),
    'success': discord.Color.green(),
    'warning': discord.Color.gold()
}

class YouTubeDownloader(commands.Cog):
    """Module de téléchargement et d'information YouTube"""
    
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
            with yt_dlp.YoutubeDL(self.get_ydl_opts("audio")) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info.get('url')
                title = info.get('title', 'Audio')
                thumbnail = info.get('thumbnail')
            
            # Extraction vidéo
            with yt_dlp.YoutubeDL(self.get_ydl_opts("video")) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
            
            return audio_url, video_url, title, thumbnail
        except Exception as e:
            logger.error(f"Erreur d'extraction: {e}")
            return None, None, None, None

    def create_embed(self, title, description="", color=None, thumbnail=None, image=None, fields=None):
        """Crée un embed Discord amélioré"""
        color = color or EmbedManager.get_default_color()
        embed = discord.Embed(
            title=title, 
            description=description or "", 
            color=color,
            timestamp=discord.utils.utcnow()
        )
        
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        if image:
            embed.set_image(url=image)
            
        if fields:
            for field in fields:
                embed.add_field(
                    name=field['name'], 
                    value=field['value'], 
                    inline=field.get('inline', False)
                )
                
        embed.set_footer(text="MathysieBot™ • YouTube Info", icon_url=self.icon_url)
        return embed

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

    def extract_video_id(self, url):
        """Extrait l'ID de la vidéo YouTube à partir de l'URL"""
        try:
            # Extraction basique de l'ID, à améliorer si nécessaire
            if "youtu.be" in url:
                return url.split("/")[-1].split("?")[0]
            elif "youtube.com/watch" in url:
                import re
                video_id_match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
                if video_id_match:
                    return video_id_match.group(1)
            return None
        except Exception:
            return None

    def format_duration(self, seconds):
        """Formate la durée en heures:minutes:secondes"""
        if not seconds:
            return "Indéterminé"
        
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def format_number(self, number):
        """Formate un nombre pour l'affichage (ex: 1000 -> 1K)"""
        if not isinstance(number, (int, float)):
            return str(number)
            
        if number < 1000:
            return str(number)
        elif number < 1000000:
            return f"{number/1000:.1f}K".replace('.0K', 'K')
        else:
            return f"{number/1000000:.1f}M".replace('.0M', 'M')

    def create_progress_bar(self, progress, length=10):
        """Crée une barre de progression visuelle avec des caractères spéciaux"""
        filled = int(progress * length)
        bar = EMOJIS['progress'] * filled + EMOJIS['empty'] * (length - filled)
        return bar

    async def update_loading_message(self, message, step, total_steps, status_text, emoji_index=0):
        """Met à jour le message de chargement avec une barre de progression"""
        progress = step / total_steps
        progress_bar = self.create_progress_bar(progress)
        percentage = int(progress * 100)
        
        embed = self.create_embed(
            f"⏳ {percentage}%",  # Utiliser un emoji fixe
            f"{progress_bar}\n\n**Statut:** {status_text}",
            color=COLORS['info']
        )
        
        await message.edit(embed=embed)
        return 0  # Retourne une valeur fixe puisque nous n'utilisons plus l'index d'emoji

    def truncate_url(self, url, max_length=500):
        """Tronque une URL si elle est trop longue"""
        if len(url) <= max_length:
            return url
        return url[:max_length] + "..."

    def parse_timestamp(self, timestamp):
        """Convertit un timestamp en secondes
        Formats acceptés: 1:23, 1:23:45, 83, 1h23m45s, etc.
        """
        if isinstance(timestamp, (int, float)):
            return int(timestamp)
        
        timestamp = str(timestamp).strip().lower()
        
        # Format: 1h23m45s
        pattern_hms = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
        match_hms = re.match(pattern_hms, timestamp)
        if match_hms and any(match_hms.groups()):
            hours = int(match_hms.group(1) or 0)
            minutes = int(match_hms.group(2) or 0)
            seconds = int(match_hms.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        
        # Format: MM:SS ou HH:MM:SS
        if ':' in timestamp:
            parts = timestamp.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
        
        # Format: nombre de secondes
        try:
            return int(float(timestamp))
        except ValueError:
            raise ValueError(f"Format de timestamp invalide: {timestamp}")

    def format_timestamp_display(self, seconds):
        """Formate un timestamp en secondes pour l'affichage"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def get_ydl_opts_with_clip(self, type: str = "audio", start_time: int = None, end_time: int = None) -> dict:
        """Retourne les options yt-dlp avec clipping"""
        base_opts = self.get_ydl_opts(type)
        
        if start_time is not None or end_time is not None:
            # Ajouter les options de postprocessing pour FFmpeg
            postprocessors = base_opts.get('postprocessors', [])
            
            # Créer les arguments FFmpeg pour le clipping
            ffmpeg_args = []
            if start_time is not None:
                ffmpeg_args.extend(['-ss', str(start_time)])
            if end_time is not None:
                duration = end_time - (start_time or 0)
                ffmpeg_args.extend(['-t', str(duration)])
            
            # Ajouter le postprocessor FFmpeg pour le clipping
            clip_processor = {
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4' if type == 'video' else 'mp3',
                'when': 'before_dl'
            }
            
            # Pour l'audio, utiliser FFmpegExtractAudio avec des options de clipping
            if type == "audio":
                audio_processor = {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192'
                }
                postprocessors = [audio_processor]
            
            base_opts['postprocessors'] = postprocessors
            
            # Ajouter les options de clipping directement dans les options de téléchargement
            if ffmpeg_args:
                base_opts['external_downloader_args'] = {
                    'ffmpeg_i': ffmpeg_args
                }
        
        return base_opts

    async def extract_info_with_clip(self, url: str, start_time: int = None, end_time: int = None) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extrait les informations de la vidéo avec clipping"""
        try:
            # D'abord, obtenir les informations de base sans télécharger
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Video')
                thumbnail = info.get('thumbnail')
                duration = info.get('duration', 0)
            
            # Valider les timestamps
            if end_time and end_time > duration:
                end_time = duration
            if start_time and start_time >= duration:
                raise ValueError("Le timestamp de début dépasse la durée de la vidéo")
            if start_time and end_time and start_time >= end_time:
                raise ValueError("Le timestamp de début doit être inférieur au timestamp de fin")
            
            # Extraction avec clipping
            audio_ydl_opts = self.get_ydl_opts_with_clip("audio", start_time, end_time)
            video_ydl_opts = self.get_ydl_opts_with_clip("video", start_time, end_time)
            
            # Obtenir les URLs directes (sans téléchargement réel)
            with yt_dlp.YoutubeDL(audio_ydl_opts) as ydl:
                audio_info = ydl.extract_info(url, download=False)
                audio_url = audio_info.get('url')
            
            with yt_dlp.YoutubeDL(video_ydl_opts) as ydl:
                video_info = ydl.extract_info(url, download=False)
                video_url = video_info.get('url')
            
            # Modifier le titre pour indiquer le clipping
            if start_time is not None or end_time is not None:
                start_display = self.format_timestamp_display(start_time) if start_time else "00:00"
                end_display = self.format_timestamp_display(end_time) if end_time else self.format_timestamp_display(duration)
                title = f"{title} [{start_display}-{end_display}]"
            
            return audio_url, video_url, title, thumbnail
            
        except Exception as e:
            logger.error(f"Erreur d'extraction avec clipping: {e}")
            return None, None, None, None

    @commands.command(
        name="ytdw",
        help="Télécharge une vidéo YouTube ou un extrait",
        description="Extrait les liens audio et vidéo d'une URL YouTube. Optionnel: spécifier un segment avec timestamps",
        usage="<url> [début] [fin]"
    )
    async def download(self, ctx: commands.Context, url: str = None, start_time: str = None, end_time: str = None):
        if not url:
            embed = self.create_embed(
                f"{EMOJIS['error']} Paramètre manquant", 
                "Veuillez fournir un lien YouTube.\n\n**Usage :** `!ytdw <lien YouTube> [début] [fin]`\n\n**Exemples de timestamps:**\n• `1:23` (1 minute 23 secondes)\n• `1:23:45` (1 heure 23 minutes 45 secondes)\n• `83` (83 secondes)\n• `1h23m45s` (format étendu)",
                color=COLORS['error']
            )
            await ctx.reply(embed=embed)
            return

        # Vérifier si c'est un lien YouTube valide
        video_id = self.extract_video_id(url)
        if not video_id:
            embed = self.create_embed(
                f"{EMOJIS['error']} Lien invalide", 
                "Veuillez fournir un lien YouTube valide.",
                color=COLORS['error']
            )
            await ctx.reply(embed=embed)
            return

        # Parser les timestamps si fournis
        parsed_start = None
        parsed_end = None
        clip_info = ""
        
        try:
            if start_time:
                parsed_start = self.parse_timestamp(start_time)
                clip_info = f"\n🎬 **Extrait demandé:** {self.format_timestamp_display(parsed_start)}"
                
            if end_time:
                parsed_end = self.parse_timestamp(end_time)
                if parsed_start:
                    clip_info = f"\n🎬 **Extrait demandé:** {self.format_timestamp_display(parsed_start)} → {self.format_timestamp_display(parsed_end)}"
                else:
                    clip_info = f"\n🎬 **Extrait demandé:** Début → {self.format_timestamp_display(parsed_end)}"
                    
        except ValueError as e:
            embed = self.create_embed(
                f"{EMOJIS['error']} Timestamp invalide", 
                f"{str(e)}\n\n**Formats acceptés:**\n• `1:23` (minutes:secondes)\n• `1:23:45` (heures:minutes:secondes)\n• `83` (secondes)\n• `1h23m45s` (format étendu)",
                color=COLORS['error']
            )
            await ctx.reply(embed=embed)
            return

        # Message de chargement initial
        loading_type = "extrait" if (parsed_start or parsed_end) else "vidéo complète"
        loading_embed = self.create_embed(
            "⏳ Initialisation", 
            f"{self.create_progress_bar(0.1)} 10%\n\nPréparation de l'analyse ({loading_type})...{clip_info}",
            color=COLORS['info']
        )
        loading_msg = await ctx.reply(embed=loading_embed)
        
        # États de progression
        loading_steps = [
            "Analyse du lien YouTube...",
            "Validation des timestamps..." if (parsed_start or parsed_end) else "Extraction des informations...",
            "Préparation du clipping..." if (parsed_start or parsed_end) else "Récupération des liens directs...",
            "Génération des liens d'extrait..." if (parsed_start or parsed_end) else "Préparation des résultats...",
            "Finalisation..."
        ]
        
        emoji_index = 0
        
        async with ctx.typing():
            try:
                # Phase 1: Analyse du lien
                emoji_index = await self.update_loading_message(loading_msg, 1, 5, loading_steps[0], emoji_index)
                await asyncio.sleep(0.5)
                
                # Phase 2: Validation/Extraction
                emoji_index = await self.update_loading_message(loading_msg, 2, 5, loading_steps[1], emoji_index)
                
                # Phase 3: Clipping/Récupération
                emoji_index = await self.update_loading_message(loading_msg, 3, 5, loading_steps[2], emoji_index)
                
                # Récupérer les informations et les liens (avec ou sans clipping)
                if parsed_start is not None or parsed_end is not None:
                    audio_url, video_url, title, thumbnail = await self.extract_info_with_clip(url, parsed_start, parsed_end)
                else:
                    audio_url, video_url, title, thumbnail = await self.extract_info(url)
                
                # Phase 4: Préparation
                emoji_index = await self.update_loading_message(loading_msg, 4, 5, loading_steps[3], emoji_index)
                await asyncio.sleep(0.5)
                
                # Phase 5: Finalisation
                await self.update_loading_message(loading_msg, 5, 5, loading_steps[4], emoji_index)
                
                if all([audio_url, video_url, title]):
                    # Ajouter des informations sur l'extrait aux embeds
                    clip_description = ""
                    if parsed_start is not None or parsed_end is not None:
                        start_display = self.format_timestamp_display(parsed_start) if parsed_start else "Début"
                        end_display = self.format_timestamp_display(parsed_end) if parsed_end else "Fin"
                        clip_description = f"\n\n🎬 **Extrait:** {start_display} → {end_display}"
                    
                    # Créer les embeds avec les liens
                    audio_embed = self.create_audio_embed(title, audio_url, thumbnail, ctx.author)
                    video_embed = self.create_video_embed(title, video_url, thumbnail, ctx.author)
                    
                    # Ajouter l'information de clipping aux embeds
                    if clip_description:
                        audio_embed.description = (audio_embed.description or "") + clip_description
                        video_embed.description = (video_embed.description or "") + clip_description
                    
                    # Envoyer les résultats
                    await loading_msg.edit(content=None, embed=audio_embed)
                    await ctx.send(embed=video_embed)
                else:
                    error_msg = "Impossible d'extraire les liens"
                    if parsed_start is not None or parsed_end is not None:
                        error_msg += " pour cet extrait"
                    error_msg += " de cette vidéo."
                    
                    error_embed = self.create_embed(
                        f"{EMOJIS['error']} Erreur", 
                        error_msg,
                        color=COLORS['error']
                    )
                    await loading_msg.edit(embed=error_embed)
                    
            except Exception as e:
                logger.error(f"Erreur YouTube Downloader: {str(e)}")
                error_embed = self.create_embed(
                    f"{EMOJIS['error']} Erreur", 
                    f"Une erreur s'est produite lors de l'extraction des liens.\n\n**Détails:** `{str(e)[:100]}...`",
                    color=COLORS['error']
                )
                await loading_msg.edit(embed=error_embed)

    @commands.command(
        name="ytsearch",
        help="Recherche des vidéos sur YouTube",
        description="Permet de rechercher des vidéos pertinentes sur YouTube en fonction des mots-clés fournis",
        usage="<mots clefs> [count]"
    )
    async def youtube_search(self, ctx, *args):
        if not args:
            embed = self.create_embed(
                f"{EMOJIS['error']} Paramètre manquant", 
                "Veuillez fournir des mots-clés à rechercher.\n\n**Usage :** `!ytsearch <mots clefs> [nombre de résultats]`",
                color=COLORS['error']
            )
            await ctx.reply(embed=embed)
            return
            
        # Vérifier si le dernier argument est un nombre (nombre de résultats)
        count = 25  # Augmenté pour avoir plusieurs pages
        search_terms = list(args)
        
        if search_terms and search_terms[-1].isdigit():
            count = int(search_terms.pop())  # Extraire le dernier élément comme count
            if count > 50:  # Limite maximale augmentée
                count = 50
        
        # Assembler les termes de recherche
        query = " ".join(search_terms)
        
        if not query:
            embed = self.create_embed(
                f"{EMOJIS['error']} Paramètre manquant", 
                "Veuillez fournir des mots-clés à rechercher.\n\n**Usage :** `!ytsearch <mots clefs> [nombre de résultats]`",
                color=COLORS['error']
            )
            await ctx.reply(embed=embed)
            return
            
        # Message de chargement initial
        loading_embed = self.create_embed(
            f"{EMOJIS['youtube']} Recherche YouTube", 
            f"Recherche en cours pour : **{query}**\n\n{self.create_progress_bar(0.2)} 20%",
            color=COLORS['info']
        )
        loading_msg = await ctx.reply(embed=loading_embed)
        
        async with ctx.typing():
            try:
                # Configuration de yt-dlp pour une recherche YouTube
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'default_search': 'ytsearch',
                    'skip_download': True,
                    'format': 'best'
                }
                
                # Mettre à jour le message de chargement
                await loading_msg.edit(embed=self.create_embed(
                    f"{EMOJIS['youtube']} Recherche YouTube", 
                    f"Recherche en cours pour : **{query}**\n\n{self.create_progress_bar(0.5)} 50%\nConsultation des serveurs YouTube...",
                    color=COLORS['info']
                ))
                
                # Effectuer la recherche
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_query = f"ytsearch{count}:{query}"
                    search_results = ydl.extract_info(search_query, download=False)
                    
                # Mettre à jour le message de chargement
                await loading_msg.edit(embed=self.create_embed(
                    f"{EMOJIS['youtube']} Recherche YouTube", 
                    f"Recherche en cours pour : **{query}**\n\n{self.create_progress_bar(0.8)} 80%\nPréparation des résultats...",
                    color=COLORS['info']
                ))
                
                # Vérifier si nous avons des résultats
                if not search_results or not search_results.get('entries'):
                    no_results_embed = self.create_embed(
                        f"{EMOJIS['warning']} Aucun résultat", 
                        f"Aucune vidéo trouvée pour la recherche : **{query}**",
                        color=COLORS['warning']
                    )
                    await loading_msg.edit(embed=no_results_embed)
                    return
                
                # Récupérer tous les résultats valides
                valid_entries = [entry for entry in search_results.get('entries', []) if entry]
                
                # Créer une fonction pour générer un embed pour une page spécifique
                def create_page_embed(page_num, entries_per_page=5):
                    start_idx = page_num * entries_per_page
                    end_idx = min(start_idx + entries_per_page, len(valid_entries))
                    current_entries = valid_entries[start_idx:end_idx]
                    
                    page_embed = discord.Embed(
                        title=f"{EMOJIS['youtube']} Résultats de recherche YouTube",
                        description=f"Recherche : **{query}**",
                        color=self.color,
                        timestamp=discord.utils.utcnow()
                    )
                    
                    # Ajouter chaque résultat à l'embed
                    for i, entry in enumerate(current_entries, start_idx + 1):
                        video_title = entry.get('title', 'Titre non disponible')
                        video_url = f"https://youtu.be/{entry.get('id')}" if entry.get('id') else 'URL non disponible'
                        
                        page_embed.add_field(
                            name=f"{i}. {video_title[:100]}{'...' if len(video_title) > 100 else ''}",
                            value=f"[Voir sur YouTube]({video_url})",
                            inline=False
                        )
                    
                    # Ajouter des informations de pagination
                    total_pages = (len(valid_entries) + entries_per_page - 1) // entries_per_page
                    page_embed.set_footer(
                        text=f"MathysieBot™ • YouTube Search | Page {page_num + 1}/{total_pages}",
                        icon_url=self.icon_url
                    )
                    
                    return page_embed
                
                # Créer les boutons de navigation
                class NavigationView(discord.ui.View):
                    def __init__(self, *, timeout=180):
                        super().__init__(timeout=timeout)
                        self.current_page = 0
                        self.entries_per_page = 5
                        self.total_pages = (len(valid_entries) + self.entries_per_page - 1) // self.entries_per_page
                    
                    @discord.ui.button(label="◀️ Précédent", style=discord.ButtonStyle.primary, disabled=True)
                    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                        self.current_page = max(0, self.current_page - 1)
                        
                        # Mettre à jour l'état des boutons
                        self.previous_button.disabled = (self.current_page == 0)
                        self.next_button.disabled = (self.current_page >= self.total_pages - 1)
                        
                        # Mettre à jour l'embed
                        await interaction.response.edit_message(
                            embed=create_page_embed(self.current_page, self.entries_per_page),
                            view=self
                        )
                    
                    @discord.ui.button(label="Suivant ▶️", style=discord.ButtonStyle.primary)
                    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                        self.current_page = min(self.total_pages - 1, self.current_page + 1)
                        
                        # Mettre à jour l'état des boutons
                        self.previous_button.disabled = (self.current_page == 0)
                        self.next_button.disabled = (self.current_page >= self.total_pages - 1)
                        
                        # Mettre à jour l'embed
                        await interaction.response.edit_message(
                            embed=create_page_embed(self.current_page, self.entries_per_page),
                            view=self
                        )
                    
                    async def on_timeout(self):
                        # Désactiver tous les boutons lorsque le délai expire
                        for item in self.children:
                            item.disabled = True
                        
                        try:
                            # Message pourrait avoir été supprimé
                            await self.message.edit(view=self)
                        except:
                            pass
                
                # Créer la vue des boutons
                view = NavigationView()
                
                # Afficher les résultats finaux avec les boutons de navigation
                await loading_msg.edit(
                    content=None,
                    embed=create_page_embed(0),
                    view=view
                )
                
                # Stocker le message pour la gestion du timeout
                view.message = loading_msg
                
            except Exception as e:
                logger.error(f"Erreur dans la recherche YouTube: {str(e)}")
                error_embed = self.create_embed(
                    f"{EMOJIS['error']} Erreur", 
                    f"Une erreur s'est produite lors de la recherche.\n\n**Détails:** `{str(e)[:100]}...`",
                    color=COLORS['error']
                )
                await loading_msg.edit(embed=error_embed)
                          
    @commands.command(
        name="ytinfo",
        help="Affiche des informations détaillées sur une vidéo YouTube",
        description="Analyse et affiche les métadonnées d'une vidéo YouTube",
        usage="<url>"
    )
    async def youtube_info(self, ctx, url=None):
        if not url:
            embed = self.create_embed(
                f"{EMOJIS['error']} Paramètre manquant", 
                "Veuillez fournir un lien YouTube.\n\n**Usage :** `!ytinfo <lien YouTube>`",
                color=COLORS['error']
            )
            await ctx.reply(embed=embed)
            return

        # Vérifier si c'est un lien YouTube valide
        video_id = self.extract_video_id(url)
        if not video_id:
            embed = self.create_embed(
                f"{EMOJIS['error']} Lien invalide", 
                "Veuillez fournir un lien YouTube valide.",
                color=COLORS['error']
            )
            await ctx.reply(embed=embed)
            return

        # Message de chargement initial
        loading_embed = self.create_embed(
            "⏳ Initialisation", 
            f"{self.create_progress_bar(0.1)} 10%\n\nPréparation de l'analyse...",
            color=COLORS['info']
        )
        loading_msg = await ctx.reply(embed=loading_embed)
        
        # États de progression pour un message évolutif
        loading_steps = [
            "Connexion aux serveurs YouTube...",
            "Récupération des métadonnées...",
            "Analyse des informations...",
            "Formatage des résultats...",
            "Finalisation..."
        ]
        
        emoji_index = 0

        async with ctx.typing():
            try:
                # Phase 1: Connexion
                emoji_index = await self.update_loading_message(loading_msg, 1, 5, loading_steps[0], emoji_index)
                await asyncio.sleep(0.5)
                
                # Phase 2: Récupération
                emoji_index = await self.update_loading_message(loading_msg, 2, 5, loading_steps[1], emoji_index)
                
                ydl_opts = {
                    'quiet': True, 
                    'no_warnings': True,
                    'skip_download': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                
                # Phase 3: Analyse
                emoji_index = await self.update_loading_message(loading_msg, 3, 5, loading_steps[2], emoji_index)
                await asyncio.sleep(0.5)
                    
                # Informations détaillées
                title = info.get('title', 'Vidéo YouTube')
                channel = info.get('uploader', 'Chaîne inconnue')
                channel_url = info.get('uploader_url', '')
                thumbnail_url = info.get('thumbnail', f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg")
                upload_date = info.get('upload_date', '')
                if upload_date:
                    upload_date = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[0:4]}"
                duration = self.format_duration(info.get('duration', 0))
                view_count = self.format_number(info.get('view_count', 'Non disponible'))
                like_count = self.format_number(info.get('like_count', 'Non disponible'))
                description = info.get('description', 'Aucune description disponible.')
                # Limiter la description à 300 caractères max
                if description and len(description) > 300:
                    description = description[:300] + "..."
                
                # Phase 4: Formatage
                emoji_index = await self.update_loading_message(loading_msg, 4, 5, loading_steps[3], emoji_index)
                await asyncio.sleep(0.5)
                
                # Phase 5: Finalisation
                await self.update_loading_message(loading_msg, 5, 5, loading_steps[4], emoji_index)
                
                # Création de l'embed détaillé
                embed = self.create_embed(
                    f"{EMOJIS['youtube']} {title}", 
                    description,
                    color=COLORS['primary'],
                    thumbnail=thumbnail_url,
                    fields=[
                        {
                            'name': f"{EMOJIS['channel']} Chaîne",
                            'value': f"[{channel}]({channel_url})" if channel_url else channel,
                            'inline': True
                        },
                        {
                            'name': f"{EMOJIS['views']} Vues",
                            'value': view_count,
                            'inline': True
                        },
                        {
                            'name': f"{EMOJIS['date']} Date",
                            'value': upload_date if upload_date else "Non disponible",
                            'inline': True
                        },
                        {
                            'name': f"{EMOJIS['duration']} Durée",
                            'value': duration,
                            'inline': True
                        },
                        {
                            'name': "👍 Likes",
                            'value': like_count,
                            'inline': True
                        },
                        {
                            'name': f"{EMOJIS['link']} Lien",
                            'value': f"[Voir sur YouTube](https://youtu.be/{video_id})",
                            'inline': True
                        },
                        {
                            'name': f"{EMOJIS['download']} Téléchargement",
                            'value': f"Pour télécharger cette vidéo, utilisez `!ytdw {url}`",
                            'inline': False
                        }
                    ]
                )
                
                await loading_msg.edit(embed=embed)
                
            except Exception as e:
                logger.error(f"Erreur lors de l'obtention des informations: {e}")
                embed = self.create_embed(
                    f"{EMOJIS['error']} Erreur", 
                    f"Une erreur s'est produite lors de la récupération des informations.\n\n**Détails:** `{str(e)[:100]}...`",
                    color=COLORS['error']
                )
                await loading_msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
    logger.info("✅ YouTube Downloader cog loaded")