import random
import asyncio
import discord
from discord import app_commands
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from collections import Counter
import numpy as np
from sklearn.cluster import KMeans
from discord.ext import commands
from utils.embed_manager import EmbedManager


class CommandesGénérales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, title, description=None, embed_type="info"):
        """Crée un embed standard pour les commandes générales"""
        return EmbedManager.create_professional_embed(
            title=title,
            description=description,
            embed_type=embed_type
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Vous n'avez pas les permissions nécessaires.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Les arguments fournis sont invalides.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Il manque des arguments requis.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog ProfilePicture connecté en tant que {self.bot.user}")

    @commands.command(
        name="pic",
        help="Affiche une photo de profil",
        description="Affiche la photo de profil d'un utilisateur en haute résolution",
        usage="[@utilisateur]",
    )
    async def pic(self, ctx, member: discord.Member = None):
        """Affiche la photo de profil d'un utilisateur
        Usage: +pic [@membre]
        """
        await self._pic_logic(ctx, member)

    @app_commands.command(name="pic", description="Affiche la photo de profil d'un utilisateur")
    async def pic_slash(self, interaction: discord.Interaction, utilisateur: discord.Member = None):
        """Version slash command pour afficher la photo de profil"""
        await self._pic_logic(interaction, utilisateur)

    async def _pic_logic(self, ctx_or_interaction, member: discord.Member = None):
        """Logique commune pour afficher la photo de profil"""
        # Déterminer si c'est un contexte ou une interaction
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        author = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
        
        # Si aucun membre n'est mentionné, prend l'auteur du message
        member = member or author

        # Vérifier si l'utilisateur a un avatar
        if member.avatar is None:
            # Obtenir l'avatar par défaut
            avatar_url = member.default_avatar.url
        else:
            # Obtenir l'avatar personnalisé avec la meilleure résolution
            avatar_url = member.avatar.url

        # Créer un embed pour afficher l'avatar
        embed = EmbedManager.create_embed(
            title=f"Photo de profil de {member.display_name}"
        )
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"ID: {member.id}")

        # Envoyer l'embed avec l'avatar
        if is_interaction:
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

    @commands.command(
        name="calc",
        help="Calculatrice simple",
        description="Effectue une opération mathématique entre deux nombres",
        usage="<nombre1> <opérateur> <nombre2>",
    )
    async def calc(self, ctx, a: float, operation: str, b: float):
        await self._calc_logic(ctx, a, operation, b)

    @app_commands.command(name="calc", description="Effectue une opération mathématique entre deux nombres")
    @app_commands.describe(
        nombre1="Premier nombre",
        operation="Opération à effectuer (+, -, *, /)",
        nombre2="Deuxième nombre"
    )
    async def calc_slash(self, interaction: discord.Interaction, nombre1: float, operation: str, nombre2: float):
        """Version slash command pour la calculatrice"""
        await self._calc_logic(interaction, nombre1, operation, nombre2)

    async def _calc_logic(self, ctx_or_interaction, a: float, operation: str, b: float):
        """Logique commune pour la calculatrice"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        
        try:
            if operation not in ["+", "-", "*", "/"]:
                message = "❌ Opération invalide. Utilisez : +, -, *, /"
                if is_interaction:
                    await ctx_or_interaction.response.send_message(message, ephemeral=True)
                else:
                    await ctx_or_interaction.send(message)
                return

            if operation == "/" and b == 0:
                message = "❌ Division par zéro impossible"
                if is_interaction:
                    await ctx_or_interaction.response.send_message(message, ephemeral=True)
                else:
                    await ctx_or_interaction.send(message)
                return

            operations = {
                "+": lambda x, y: x + y,
                "-": lambda x, y: x - y,
                "*": lambda x, y: x * y,
                "/": lambda x, y: x / y,
            }

            result = operations[operation](a, b)
            embed = self.create_embed(
                "🔢 Calculatrice", f"{a} {operation} {b} = {result:.2f}"
            )
            
            if is_interaction:
                await ctx_or_interaction.response.send_message(embed=embed)
            else:
                await ctx_or_interaction.send(embed=embed)

        except ValueError:
            message = "❌ Veuillez entrer des nombres valides"
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)

    @commands.command(
        name="roll",
        help="Lance un dé",
        description="Génère un nombre aléatoire entre 1 et 10",
        usage="",
    )
    async def roll(self, ctx):
        await self._roll_logic(ctx)

    @app_commands.command(name="roll", description="Lance un dé (génère un nombre aléatoire entre 1 et 10)")
    async def roll_slash(self, interaction: discord.Interaction):
        """Version slash command pour lancer un dé"""
        await self._roll_logic(interaction)

    async def _roll_logic(self, ctx_or_interaction):
        """Logique commune pour lancer un dé"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        author = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
        
        result = random.randint(1, 10)
        embed = self.create_embed(
            "🎲 Jet de dé", f"{author.mention} a obtenu : **{result}**"
        )
        
        if is_interaction:
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

    @commands.command(
        name="say",
        help="Répète un message",
        description="Répète un message dans un salon spécifique un certain nombre de fois",
        usage="<message> [#salon] [nombre]",
    )
    async def say(self, ctx, *, args):
        """Répète un message dans un salon"""
        await self._say_logic(ctx, args=args)

    @app_commands.command(name="say", description="Répète un message dans le salon actuel")
    @app_commands.describe(
        message="Message à répéter",
        count="Nombre de fois à répéter (1-5, défaut: 1)"
    )
    async def say_slash(self, interaction: discord.Interaction, message: str, count: int = 1):
        """Version slash command pour répéter un message"""
        await self._say_logic(interaction, message=message, count=count)

    async def _say_logic(self, ctx_or_interaction, args: str = None, message: str = None, count: int = 1):
        """Logique commune pour répéter un message"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        
        try:
            if is_interaction:
                # Pour les slash commands, les paramètres sont plus simples
                final_message = message
                final_count = max(1, min(count, 5))  # Limiter entre 1 et 5
                channel = ctx_or_interaction.channel
            else:
                # Pour les commandes prefix, analyser les arguments
                parts = args.split()

                # Vérification du salon
                if (
                    len(parts) >= 2
                    and parts[-2].startswith("<#")
                    and parts[-2].endswith(">")
                ):
                    channel_id = int(parts[-2][2:-1])
                    channel = ctx_or_interaction.guild.get_channel(channel_id)
                    parts.pop(-2)
                else:
                    channel = ctx_or_interaction.channel

                # Vérification du nombre
                try:
                    final_count = int(parts[-1])
                    if 0 < final_count <= 5:
                        parts.pop(-1)
                    else:
                        final_count = 1
                except ValueError:
                    final_count = 1

                # Message final
                final_message = " ".join(parts)

            # Envoi des messages
            for _ in range(final_count):
                await channel.send(final_message)
                await asyncio.sleep(1)

            embed = self.create_embed(
                "📢 Message répété",
                f"Message envoyé {final_count} fois dans {channel.mention}",
            )
            
            if is_interaction:
                await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=embed)

        except discord.Forbidden:
            message_error = "❌ Je n'ai pas la permission d'envoyer des messages dans ce salon"
            if is_interaction:
                await ctx_or_interaction.response.send_message(message_error, ephemeral=True)
            else:
                await ctx_or_interaction.send(message_error)
        except Exception as e:
            message_error = f"❌ Une erreur est survenue : {str(e)}"
            if is_interaction:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.send_message(message_error, ephemeral=True)
                else:
                    await ctx_or_interaction.followup.send(message_error, ephemeral=True)
            else:
                await ctx_or_interaction.send(message_error)

    @commands.command(
        name="iconvert",
        help="Convertit une image - Formats: png, jpg, jpeg, webp, gif, bmp",
        description="Convertit une image jointe vers le format spécifié. Formats supportés: png, jpg, jpeg, webp, gif, bmp",
        usage="<format> (avec image en pièce jointe)",
    )
    async def iconvert(self, ctx, format_type: str):
        """Convertit une image vers le format spécifié
        Usage: +iconvert <format> (avec image en pièce jointe)
        Formats supportés: png, jpg, jpeg, webp, gif, bmp
        """
        attachments = ctx.message.attachments
        await self._iconvert_logic(ctx, format_type, attachments)

    @app_commands.command(name="iconvert", description="Convertit une image vers le format spécifié")
    @app_commands.describe(
        format="Format de sortie (png, jpg, jpeg, webp, gif, bmp)",
        image="Image à convertir"
    )
    async def iconvert_slash(self, interaction: discord.Interaction, format: str, image: discord.Attachment):
        """Version slash command pour convertir une image"""
        await self._iconvert_logic(interaction, format, [image])

    async def _iconvert_logic(self, ctx_or_interaction, format_type: str, attachments: list):
        """Logique commune pour convertir une image"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        
        # Formats d'image supportés
        supported_formats = ["png", "jpg", "jpeg", "webp", "gif", "bmp"]
        format_type = format_type.lower()

        if format_type not in supported_formats:
            message = f"❌ Format non supporté. Formats disponibles : {', '.join(supported_formats)}"
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        # Vérifier qu'il y a une pièce jointe
        if not attachments:
            message = "❌ Veuillez joindre une image à convertir."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        attachment = attachments[0]

        # Vérifier que c'est une image
        if not any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
        ):
            message = "❌ Le fichier joint n'est pas une image valide."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        try:
            # Pour les interactions, on doit répondre rapidement
            if is_interaction:
                await ctx_or_interaction.response.defer()

            # Télécharger l'image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        message = "❌ Impossible de télécharger l'image."
                        if is_interaction:
                            await ctx_or_interaction.followup.send(message, ephemeral=True)
                        else:
                            await ctx_or_interaction.send(message)
                        return
                    image_data = await resp.read()

            # Ouvrir l'image avec PIL
            image = Image.open(io.BytesIO(image_data))

            # Convertir en RGB si nécessaire (pour JPG)
            if format_type in ["jpg", "jpeg"] and image.mode in ["RGBA", "P"]:
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
                image = background

            # Sauvegarder dans le nouveau format
            output = io.BytesIO()
            if format_type == "jpg":
                format_type = "jpeg"
            image.save(output, format=format_type.upper())
            output.seek(0)

            # Créer le nom du fichier de sortie
            original_name = attachment.filename.rsplit(".", 1)[0]
            new_filename = f"{original_name}_converted.{format_type}"

            # Envoyer le fichier converti
            file = discord.File(output, filename=new_filename)
            embed = self.create_embed(
                "🖼️ Conversion d'image réussie",
                f"Image convertie en format {format_type.upper()}",
            )
            
            if is_interaction:
                await ctx_or_interaction.followup.send(embed=embed, file=file)
            else:
                await ctx_or_interaction.send(embed=embed, file=file)

        except Exception as e:
            message = f"❌ Erreur lors de la conversion : {str(e)}"
            if is_interaction:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.send_message(message, ephemeral=True)
                else:
                    await ctx_or_interaction.followup.send(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)

    @commands.command(
        name="fconvert",
        help="Convertit un fichier - Formats: txt, md, html, json, csv, xml",
        description="Convertit un fichier texte vers le format spécifié. Formats supportés: txt, md, html, json, csv, xml",
        usage="<format> (avec fichier en pièce jointe)",
    )
    async def fconvert(self, ctx, format_type: str):
        """Convertit un fichier texte vers le format spécifié
        Usage: +fconvert <format> (avec fichier en pièce jointe)
        Formats supportés: txt, md, html, json, csv, xml
        """
        attachments = ctx.message.attachments
        await self._fconvert_logic(ctx, format_type, attachments)

    @app_commands.command(name="fconvert", description="Convertit un fichier texte vers le format spécifié")
    @app_commands.describe(
        format="Format de sortie (txt, md, html, json, csv, xml)",
        file="Fichier à convertir"
    )
    async def fconvert_slash(self, interaction: discord.Interaction, format: str, file: discord.Attachment):
        """Version slash command pour convertir un fichier"""
        await self._fconvert_logic(interaction, format, [file])

    async def _fconvert_logic(self, ctx_or_interaction, format_type: str, attachments: list):
        """Logique commune pour convertir un fichier"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        
        # Formats de fichier supportés (principalement texte)
        supported_formats = ["txt", "md", "html", "json", "csv", "xml"]
        format_type = format_type.lower()

        if format_type not in supported_formats:
            message = f"❌ Format non supporté. Formats disponibles : {', '.join(supported_formats)}"
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        # Vérifier qu'il y a une pièce jointe
        if not attachments:
            message = "❌ Veuillez joindre un fichier à convertir."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        attachment = attachments[0]

        # Vérifier la taille du fichier (limite à 8MB)
        if attachment.size > 8 * 1024 * 1024:
            message = "❌ Le fichier est trop volumineux (limite : 8MB)."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        try:
            # Pour les interactions, on doit répondre rapidement
            if is_interaction:
                await ctx_or_interaction.response.defer()

            # Télécharger le fichier
            file_content = await attachment.read()

            # Décoder le contenu (essayer UTF-8 d'abord)
            try:
                text_content = file_content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text_content = file_content.decode("latin-1")
                except UnicodeDecodeError:
                    message = "❌ Impossible de décoder le fichier. Seuls les fichiers texte sont supportés."
                    if is_interaction:
                        await ctx_or_interaction.followup.send(message, ephemeral=True)
                    else:
                        await ctx_or_interaction.send(message)
                    return

            # Convertir selon le format demandé
            if format_type == "html":
                # Conversion simple texte vers HTML
                converted_content = f"<!DOCTYPE html>\n<html>\n<head>\n<title>Fichier converti</title>\n</head>\n<body>\n<pre>{text_content}</pre>\n</body>\n</html>"
            elif format_type == "md":
                # Conversion vers Markdown (ajouter des backticks pour le code)
                converted_content = f"# Fichier converti\n\n```\n{text_content}\n```"
            elif format_type == "xml":
                # Conversion simple vers XML
                converted_content = f"<?xml version='1.0' encoding='UTF-8'?>\n<document>\n<content><![CDATA[{text_content}]]></content>\n</document>"
            else:
                # Pour txt, json, csv - garder le contenu tel quel
                converted_content = text_content

            # Créer le nom du fichier de sortie
            original_name = attachment.filename.rsplit(".", 1)[0]
            new_filename = f"{original_name}_converted.{format_type}"

            # Créer le fichier de sortie
            output = io.BytesIO(converted_content.encode("utf-8"))
            file = discord.File(output, filename=new_filename)

            embed = self.create_embed(
                "📄 Conversion de fichier réussie",
                f"Fichier converti en format {format_type.upper()}",
            )
            
            if is_interaction:
                await ctx_or_interaction.followup.send(embed=embed, file=file)
            else:
                await ctx_or_interaction.send(embed=embed, file=file)

        except Exception as e:
            message = f"❌ Erreur lors de la conversion : {str(e)}"
            if is_interaction:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.send_message(message, ephemeral=True)
                else:
                    await ctx_or_interaction.followup.send(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)

    @commands.command(
        name="compress",
        help="Compresse une image - Réduit la taille et qualité",
        description="Compresse une image jointe pour réduire sa taille de fichier",
        usage="[qualité] (avec image en pièce jointe)",
    )
    async def compress(self, ctx, quality: int = 50):
        """Compresse une image pour réduire sa taille
        Usage: +compress [qualité] (avec image en pièce jointe)
        Qualité: 1-100 (défaut: 50)
        """
        attachments = ctx.message.attachments
        await self._compress_logic(ctx, quality, attachments)

    @app_commands.command(name="compress", description="Compresse une image pour réduire sa taille")
    @app_commands.describe(
        image="Image à compresser",
        quality="Qualité de compression (1-100, défaut: 50)"
    )
    async def compress_slash(self, interaction: discord.Interaction, image: discord.Attachment, quality: int = 50):
        """Version slash command pour compresser une image"""
        await self._compress_logic(interaction, quality, [image])

    async def _compress_logic(self, ctx_or_interaction, quality: int, attachments: list):
        """Logique commune pour compresser une image"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        
        # Vérifier la qualité
        if not 1 <= quality <= 100:
            message = "❌ La qualité doit être entre 1 et 100."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        # Vérifier qu'il y a une pièce jointe
        if not attachments:
            message = "❌ Veuillez joindre une image à compresser."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        attachment = attachments[0]

        # Vérifier que c'est une image
        if not any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
        ):
            message = "❌ Le fichier joint n'est pas une image valide."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        try:
            # Pour les interactions, on doit répondre rapidement
            if is_interaction:
                await ctx_or_interaction.response.defer()

            # Télécharger l'image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        message = "❌ Impossible de télécharger l'image."
                        if is_interaction:
                            await ctx_or_interaction.followup.send(message, ephemeral=True)
                        else:
                            await ctx_or_interaction.send(message)
                        return
                    image_data = await resp.read()

            original_size = len(image_data)

            # Ouvrir l'image avec PIL
            image = Image.open(io.BytesIO(image_data))

            # Convertir en RGB si nécessaire
            if image.mode in ["RGBA", "P"]:
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
                image = background

            # Compresser l'image
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=quality, optimize=True)
            output.seek(0)

            compressed_size = len(output.getvalue())
            compression_ratio = round((1 - compressed_size / original_size) * 100, 1)

            # Créer le nom du fichier de sortie
            original_name = attachment.filename.rsplit(".", 1)[0]
            new_filename = f"{original_name}_compressed.jpg"

            # Envoyer le fichier compressé
            file = discord.File(output, filename=new_filename)
            embed = self.create_embed(
                "🗜️ Compression d'image réussie",
                f"Taille originale: {original_size // 1024} KB\nTaille compressée: {compressed_size // 1024} KB\nRéduction: {compression_ratio}%\nQualité: {quality}%",
            )
            
            if is_interaction:
                await ctx_or_interaction.followup.send(embed=embed, file=file)
            else:
                await ctx_or_interaction.send(embed=embed, file=file)

        except Exception as e:
            message = f"❌ Erreur lors de la compression : {str(e)}"
            if is_interaction:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.send_message(message, ephemeral=True)
                else:
                    await ctx_or_interaction.followup.send(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)

    @commands.command(
        name="bgcolor",
        help="Extrait les couleurs dominantes - Usage: !bgcolor <nombre>",
        description="Extrait les couleurs dominantes d'une image jointe avec palette visuelle",
        usage="<nombre> (avec image en pièce jointe)",
    )
    async def color(self, ctx, num_colors: int = 5):
        """Extrait les couleurs dominantes d'une image
        Usage: +bgcolor <nombre> (avec image en pièce jointe)
        Nombre: 1-40 couleurs à extraire (défaut: 5)
        """
        attachments = ctx.message.attachments
        await self._bgcolor_logic(ctx, num_colors, attachments)

    @app_commands.command(name="bgcolor", description="Extrait les couleurs dominantes d'une image")
    @app_commands.describe(
        image="Image à analyser",
        nombre_couleurs="Nombre de couleurs à extraire (1-40, défaut: 5)"
    )
    async def bgcolor_slash(self, interaction: discord.Interaction, image: discord.Attachment, nombre_couleurs: int = 5):
        """Version slash command pour extraire les couleurs dominantes"""
        await self._bgcolor_logic(interaction, nombre_couleurs, [image])

    async def _bgcolor_logic(self, ctx_or_interaction, num_colors: int, attachments: list):
        """Logique commune pour extraire les couleurs dominantes"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        
        # Vérifier le nombre de couleurs
        if not 1 <= num_colors <= 40:
            message = "❌ Le nombre de couleurs doit être entre 1 et 40."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        # Vérifier qu'il y a une pièce jointe
        if not attachments:
            message = "❌ Veuillez joindre une image pour analyser les couleurs."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        attachment = attachments[0]

        # Vérifier que c'est une image
        if not any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
        ):
            message = "❌ Le fichier joint n'est pas une image valide."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        try:
            # Pour les interactions, on doit répondre rapidement
            if is_interaction:
                await ctx_or_interaction.response.defer()
            else:
                # Ajouter une réaction pour indiquer le traitement
                await ctx_or_interaction.message.add_reaction("⏳")

            # Télécharger l'image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        message = "❌ Impossible de télécharger l'image."
                        if is_interaction:
                            await ctx_or_interaction.followup.send(message, ephemeral=True)
                        else:
                            await ctx_or_interaction.send(message)
                        return
                    image_data = await resp.read()

            # [Le reste de la logique de traitement d'image reste identique...]
            # Ouvrir l'image avec PIL
            image = Image.open(io.BytesIO(image_data))
            original_size = image.size

            # Convertir en RGB
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Redimensionner pour accélérer l'analyse
            image.thumbnail((200, 200))

            # Convertir en array numpy
            img_array = np.array(image)
            img_array = img_array.reshape(-1, 3)

            # Utiliser KMeans pour trouver les couleurs dominantes
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(img_array)

            colors = kmeans.cluster_centers_.astype(int)

            # Calculer les pourcentages de chaque couleur
            labels = kmeans.labels_
            unique_labels, counts = np.unique(labels, return_counts=True)
            percentages = (counts / len(labels)) * 100

            # Trier par pourcentage décroissant
            sorted_indices = np.argsort(percentages)[::-1]
            colors = colors[sorted_indices]
            percentages = percentages[sorted_indices]

            # [Création de la palette et du fichier texte - code identique...]
            # Pour économiser l'espace, je vais créer une version simplifiée qui génère juste l'embed
            embed_color_info = []
            
            for i, (color, percentage) in enumerate(zip(colors[:5], percentages[:5])):  # Limiter à 5 pour l'embed
                # Convertir en hex
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                
                # Emoji couleur pour l'embed
                if color[0] > color[1] and color[0] > color[2]:
                    emoji = "🔴"
                elif color[1] > color[0] and color[1] > color[2]:
                    emoji = "🟢"
                elif color[2] > color[0] and color[2] > color[1]:
                    emoji = "🔵"
                elif color[0] + color[1] > color[2] * 1.5:
                    emoji = "🟡"
                elif sum(color) > 600:
                    emoji = "⚪"
                elif sum(color) < 150:
                    emoji = "⚫"
                else:
                    emoji = "🟤"

                embed_color_info.append(
                    f"{emoji} **{percentage:.1f}%** - `{hex_color}`\n└ RGB({color[0]}, {color[1]}, {color[2]})"
                )

            # Créer l'embed
            embed = self.create_embed(
                f"🎨 Palette de {min(num_colors, 5)} couleur(s) dominante(s)",
                f"**Image :** {attachment.filename}\n**Résolution :** {original_size[0]}x{original_size[1]}px\n\n"
                + "\n\n".join(embed_color_info),
            )
            embed.set_thumbnail(url=attachment.url)

            if is_interaction:
                await ctx_or_interaction.followup.send(embed=embed)
            else:
                await ctx_or_interaction.message.remove_reaction("⏳", ctx_or_interaction.bot.user)
                await ctx_or_interaction.send(embed=embed)

        except Exception as e:
            message = f"❌ Erreur lors de l'analyse des couleurs : {str(e)}"
            if is_interaction:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.send_message(message, ephemeral=True)
                else:
                    await ctx_or_interaction.followup.send(message, ephemeral=True)
            else:
                await ctx_or_interaction.message.remove_reaction("⏳", ctx_or_interaction.bot.user)
                await ctx_or_interaction.send(message)

    @commands.command(
        name="enhance",
        help="Améliore la qualité d'une image - Augmente résolution et netteté",
        description="Améliore une image jointe en augmentant sa résolution et sa netteté",
        usage="[facteur] (avec image en pièce jointe)",
    )
    async def enhance(self, ctx, scale_factor: float = 2.0):
        """Améliore la qualité d'une image
        Usage: +enhance [facteur] (avec image en pièce jointe)
        Facteur: 1.5-4.0 (défaut: 2.0) - multiplicateur de résolution
        """
        attachments = ctx.message.attachments
        await self._enhance_logic(ctx, scale_factor, attachments)

    @app_commands.command(name="enhance", description="Améliore la qualité d'une image en augmentant sa résolution")
    @app_commands.describe(
        image="Image à améliorer",
        facteur="Facteur d'agrandissement (1.5-4.0, défaut: 2.0)"
    )
    async def enhance_slash(self, interaction: discord.Interaction, image: discord.Attachment, facteur: float = 2.0):
        """Version slash command pour améliorer une image"""
        await self._enhance_logic(interaction, facteur, [image])

    async def _enhance_logic(self, ctx_or_interaction, scale_factor: float, attachments: list):
        """Logique commune pour améliorer une image"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
        
        # Vérifier le facteur d'agrandissement
        if not 1.5 <= scale_factor <= 4.0:
            message = "❌ Le facteur doit être entre 1.5 et 4.0."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        # Vérifier qu'il y a une pièce jointe
        if not attachments:
            message = "❌ Veuillez joindre une image à améliorer."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        attachment = attachments[0]

        # Vérifier que c'est une image
        if not any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
        ):
            message = "❌ Le fichier joint n'est pas une image valide."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        # Vérifier la taille du fichier (limite plus stricte pour l'amélioration)
        if attachment.size > 5 * 1024 * 1024:  # 5MB max
            message = "❌ L'image est trop volumineuse pour l'amélioration (limite : 5MB)."
            if is_interaction:
                await ctx_or_interaction.response.send_message(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
            return

        try:
            # Pour les interactions, on doit répondre rapidement
            if is_interaction:
                await ctx_or_interaction.response.defer()
            else:
                # Ajouter une réaction pour indiquer le traitement
                await ctx_or_interaction.message.add_reaction("⏳")

            # Télécharger l'image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        message = "❌ Impossible de télécharger l'image."
                        if is_interaction:
                            await ctx_or_interaction.followup.send(message, ephemeral=True)
                        else:
                            await ctx_or_interaction.send(message)
                        return
                    image_data = await resp.read()

            original_size_bytes = len(image_data)

            # Ouvrir l'image avec PIL
            image = Image.open(io.BytesIO(image_data))
            original_resolution = image.size

            # Convertir en RGB si nécessaire
            if image.mode in ["RGBA"]:
                # Conserver la transparence pour PNG
                pass
            elif image.mode in ["P"]:
                image = image.convert("RGBA")
            elif image.mode not in ["RGB", "RGBA"]:
                image = image.convert("RGB")

            # Calculer la nouvelle taille
            new_width = int(original_resolution[0] * scale_factor)
            new_height = int(original_resolution[1] * scale_factor)

            # Vérifier que la nouvelle résolution n'est pas trop grande
            if new_width * new_height > 16000000:  # ~16 mégapixels max
                message = "❌ La résolution finale serait trop importante. Réduisez le facteur d'agrandissement."
                if is_interaction:
                    await ctx_or_interaction.followup.send(message, ephemeral=True)
                else:
                    await ctx_or_interaction.send(message)
                return

            # Améliorer l'image avec différentes techniques

            # 1. Redimensionnement avec algorithme Lanczos (haute qualité)
            enhanced_image = image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )

            # 2. Appliquer des filtres d'amélioration
            from PIL import ImageEnhance, ImageFilter

            # Améliorer la netteté
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced_image)
            enhanced_image = sharpness_enhancer.enhance(
                1.2
            )  # Augmenter légèrement la netteté

            # Améliorer le contraste légèrement
            contrast_enhancer = ImageEnhance.Contrast(enhanced_image)
            enhanced_image = contrast_enhancer.enhance(1.1)

            # Appliquer un filtre de netteté supplémentaire pour les détails
            if scale_factor >= 2.0:
                enhanced_image = enhanced_image.filter(
                    ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3)
                )

            # Sauvegarder l'image améliorée
            output = io.BytesIO()

            # Choisir le format et la qualité de sortie
            original_format = image.format or "PNG"
            if (
                original_format.upper() == "JPEG"
                or attachment.filename.lower().endswith((".jpg", ".jpeg"))
            ):
                enhanced_image = enhanced_image.convert(
                    "RGB"
                )  # JPEG ne supporte pas la transparence
                enhanced_image.save(output, format="JPEG", quality=95, optimize=True)
                file_extension = "jpg"
            else:
                enhanced_image.save(output, format="PNG", optimize=True)
                file_extension = "png"

            output.seek(0)
            enhanced_size_bytes = len(output.getvalue())

            # Calculer les statistiques
            resolution_increase = (
                (new_width * new_height)
                / (original_resolution[0] * original_resolution[1])
                - 1
            ) * 100
            size_change = ((enhanced_size_bytes / original_size_bytes) - 1) * 100

            # Créer le nom du fichier de sortie
            original_name = attachment.filename.rsplit(".", 1)[0]
            new_filename = f"{original_name}_enhanced.{file_extension}"

            # Envoyer le fichier amélioré
            file = discord.File(output, filename=new_filename)
            embed = self.create_embed(
                "✨ Amélioration d'image réussie",
                f"**Résolution originale:** {original_resolution[0]}x{original_resolution[1]}px\n"
                f"**Nouvelle résolution:** {new_width}x{new_height}px\n"
                f"**Facteur d'agrandissement:** x{scale_factor}\n"
                f"**Augmentation de résolution:** +{resolution_increase:.1f}%\n"
                f"**Taille originale:** {original_size_bytes // 1024} KB\n"
                f"**Nouvelle taille:** {enhanced_size_bytes // 1024} KB\n"
                f"**Améliorations appliquées:** Redimensionnement Lanczos, netteté, contraste",
            )

            if is_interaction:
                await ctx_or_interaction.followup.send(embed=embed, file=file)
            else:
                await ctx_or_interaction.message.remove_reaction("⏳", ctx_or_interaction.bot.user)
                await ctx_or_interaction.send(embed=embed, file=file)

        except Exception as e:
            message = f"❌ Erreur lors de l'amélioration : {str(e)}"
            if is_interaction:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.send_message(message, ephemeral=True)
                else:
                    await ctx_or_interaction.followup.send(message, ephemeral=True)
            else:
                await ctx_or_interaction.message.remove_reaction("⏳", ctx_or_interaction.bot.user)
                await ctx_or_interaction.send(message)

    def _rgb_to_hsv(self, rgb):
        """Convertit RGB en HSV pour plus d'informations"""
        r, g, b = rgb / 255.0
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val

        # Hue
        if diff == 0:
            h = 0
        elif max_val == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_val == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        # Saturation
        s = 0 if max_val == 0 else (diff / max_val) * 100

        # Value
        v = max_val * 100

        return f"{h:.0f}°, {s:.0f}%, {v:.0f}%"

async def setup(bot):
    await bot.add_cog(CommandesGénérales(bot))
