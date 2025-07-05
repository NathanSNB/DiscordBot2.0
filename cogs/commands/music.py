import discord
from discord.ext import commands, tasks
import yt_dlp as youtube_dl
import asyncio
import logging
from utils.embed_manager import EmbedManager

logger = logging.getLogger("bot")  # Configuration du logger


class Commandes_musicales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_track = None  # Variable pour suivre la musique en cours
        self.queue = []  # File d'attente pour la lecture des pistes
        self.inactivity_check.start()  # Lancer la vérification d'inactivité

    @tasks.loop(minutes=1)
    async def inactivity_check(self):
        """Vérifie l'inactivité des utilisateurs dans le salon vocal."""
        for guild in self.bot.guilds:
            voice_client = guild.voice_client
            if voice_client and voice_client.channel.members:
                # Si le bot est dans un salon vocal et qu'il y a des membres présents
                if (
                    len(voice_client.channel.members) == 1
                ):  # Vérifie si seul le bot est présent
                    await voice_client.disconnect()

    def create_embed(self, title, description=None, embed_type="music"):
        """Crée un embed standard pour les réponses musicales."""
        return EmbedManager.create_professional_embed(
            title=title, description=description, embed_type=embed_type
        )

    async def _send_response(
        self, ctx, message, title="Système Musical", embed_type="music"
    ):
        """Envoie une réponse avec un embed professionnel."""
        try:
            embed = EmbedManager.create_professional_embed(
                title=title, description=message, embed_type=embed_type
            )
            if isinstance(ctx, discord.Interaction):
                return await ctx.followup.send(embed=embed)
            else:
                return await ctx.send(embed=embed)
        except discord.HTTPException as e:
            print(f"⚠️ Erreur HTTP lors de l'envoi de la réponse : {e}")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'envoi de la réponse : {e}")

    @commands.hybrid_command(
        name="play",
        description="Joue la musique depuis une URL YouTube ou une playlist.",
    )
    async def play(self, ctx, url: str):
        """Joue la musique à partir d'une URL YouTube (chanson ou playlist)."""
        # Déférer l'interaction immédiatement pour éviter qu'elle expire
        if isinstance(ctx, discord.Interaction) and not ctx.response.is_done():
            await ctx.response.defer()

        # Vérifier si l'utilisateur est dans un salon vocal
        if not ctx.author.voice:
            response_message = (
                "❌ Vous devez être dans un salon vocal pour jouer de la musique."
            )
            await self._send_response(ctx, response_message)
            return

        # Vérifier si l'URL est valide
        if not url.startswith("http"):
            response_message = "❌ Veuillez fournir une URL valide pour la musique."
            await self._send_response(ctx, response_message)
            return

        voice_channel = ctx.author.voice.channel
        voice_client = ctx.guild.voice_client

        try:
            # Connecter le bot au salon vocal
            if voice_client is None or not voice_client.is_connected():
                voice_client = await voice_channel.connect()
            elif voice_client.channel != voice_channel:
                # Déplacer le bot si l'utilisateur est dans un autre canal vocal
                await voice_client.move_to(voice_channel)

            # Vérifier si l'URL est une playlist
            if "playlist" in url:
                await self.play_playlist(url, voice_client, ctx)
            else:
                await self.play_music(url, voice_client)

            # Sauvegarder le dernier message du bot contenant le lien
            self.last_message = await self._send_response(
                ctx, f"🎵 En train de jouer : **{url}**"
            )
        except discord.ClientException as e:
            response_message = f"❌ Erreur de connexion au salon vocal : {e}"
            await self._send_response(ctx, response_message)
        except Exception as e:
            response_message = (
                f"❌ Une erreur est survenue lors de la lecture de la musique : {e}"
            )
            await self._send_response(ctx, response_message)

    async def play_playlist(self, url, voice_client, ctx):
        """Joue la playlist entière en enchaînant les vidéos."""
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "nocheckcertificate": True,
            "extract_flat": True,  # Pour éviter de télécharger les vidéos, juste l'audio
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            playlist_title = info.get("title", "Playlist inconnue")
            videos = info["entries"]

            # Ajouter chaque vidéo à la queue
            for video in videos:
                self.queue.append(video["url"])

            # Joue la première vidéo
            await self.play_music(self.queue.pop(0), voice_client)

            # Indiquer la playlist en cours
            await self._send_response(
                ctx,
                f"🎶 Playlist en cours : {playlist_title}",
                title="Lecture de Playlist",
            )

    async def play_music(self, url, voice_client):
        """Joue la musique via FFmpeg."""
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "opus",
                    "preferredquality": "320",
                }
            ],
            "quiet": True,
            "nocheckcertificate": True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]

            source = discord.FFmpegPCMAudio(audio_url, executable="ffmpeg")
            if not voice_client.is_playing():
                voice_client.play(
                    source,
                    after=lambda e: asyncio.run(self.handle_audio_end(e, voice_client)),
                )

    async def handle_audio_end(self, error, voice_client):
        """Gestion de la fin de la musique."""
        if error:
            print(f"Erreur de lecture : {error}")
        if self.queue:
            next_track = self.queue.pop(0)
            await self.play_music(next_track, voice_client)
        else:
            await voice_client.disconnect()

    @commands.hybrid_command(
        name="stop", description="Arrête la musique et déconnecte le bot."
    )
    async def stop(self, ctx):
        """Arrête la musique et déconnecte le bot."""
        if isinstance(ctx, discord.Interaction) and not ctx.response.is_done():
            await ctx.response.defer()

        voice_client = ctx.guild.voice_client

        if voice_client and voice_client.is_playing():
            # Récupérer l'URL ou le nom de la musique en cours
            current_track = self.current_track or "inconnue"
            voice_client.stop()
            await voice_client.disconnect()
            response_message = f"⏹️ La musique **{current_track}** a été arrêtée et le bot a quitté le salon vocal."
        elif voice_client:
            await voice_client.disconnect()
            response_message = "🔇 Le bot a quitté le salon vocal."
        else:
            response_message = "❌ Le bot n'est pas connecté à un salon vocal."

        await self._send_response(ctx, response_message, title="Musique Arrêtée")


# Ajout de la cog
async def setup(bot):
    """Ajoute la cog Commandes_musicales au bot."""
    await bot.add_cog(Commandes_musicales(bot))
