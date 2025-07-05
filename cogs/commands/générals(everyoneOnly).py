import random
import asyncio
import discord
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
        # Si aucun membre n'est mentionné, prend l'auteur du message
        member = member or ctx.author

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
        await ctx.send(embed=embed)

    @commands.command(
        name="calc",
        help="Calculatrice simple",
        description="Effectue une opération mathématique entre deux nombres",
        usage="<nombre1> <opérateur> <nombre2>",
    )
    async def calc(self, ctx, a: float, operation: str, b: float):
        try:
            if operation not in ["+", "-", "*", "/"]:
                await ctx.send("❌ Opération invalide. Utilisez : +, -, *, /")
                return

            if operation == "/" and b == 0:
                await ctx.send("❌ Division par zéro impossible")
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
            await ctx.send(embed=embed)

        except ValueError:
            await ctx.send("❌ Veuillez entrer des nombres valides")

    @commands.command(
        name="roll",
        help="Lance un dé",
        description="Génère un nombre aléatoire entre 1 et 10",
        usage="",
    )
    async def roll(self, ctx):
        result = random.randint(1, 10)
        embed = self.create_embed(
            "🎲 Jet de dé", f"{ctx.author.mention} a obtenu : **{result}**"
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="say",
        help="Répète un message",
        description="Répète un message dans un salon spécifique un certain nombre de fois",
        usage="<message> [#salon] [nombre]",
    )
    async def say(self, ctx, *, args):
        """Répète un message dans un salon"""
        try:
            # Extraction des arguments
            parts = args.split()

            # Vérification du salon
            if (
                len(parts) >= 2
                and parts[-2].startswith("<#")
                and parts[-2].endswith(">")
            ):
                channel_id = int(parts[-2][2:-1])
                channel = ctx.guild.get_channel(channel_id)
                parts.pop(-2)
            else:
                channel = ctx.channel

            # Vérification du nombre
            try:
                count = int(parts[-1])
                if 0 < count <= 5:
                    parts.pop(-1)
                else:
                    count = 1
            except ValueError:
                count = 1

            # Message final
            message = " ".join(parts)

            # Envoi des messages
            for _ in range(count):
                await channel.send(message)
                await asyncio.sleep(1)

            embed = self.create_embed(
                "📢 Message répété",
                f"Message envoyé {count} fois dans {channel.mention}",
            )
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send(
                "❌ Je n'ai pas la permission d'envoyer des messages dans ce salon"
            )
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

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
        # Formats d'image supportés
        supported_formats = ["png", "jpg", "jpeg", "webp", "gif", "bmp"]
        format_type = format_type.lower()

        if format_type not in supported_formats:
            await ctx.send(
                f"❌ Format non supporté. Formats disponibles : {', '.join(supported_formats)}"
            )
            return

        # Vérifier qu'il y a une pièce jointe
        if not ctx.message.attachments:
            await ctx.send("❌ Veuillez joindre une image à convertir.")
            return

        attachment = ctx.message.attachments[0]

        # Vérifier que c'est une image
        if not any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
        ):
            await ctx.send("❌ Le fichier joint n'est pas une image valide.")
            return

        try:
            # Télécharger l'image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        await ctx.send("❌ Impossible de télécharger l'image.")
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
            await ctx.send(embed=embed, file=file)

        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la conversion : {str(e)}")

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
        # Formats de fichier supportés (principalement texte)
        supported_formats = ["txt", "md", "html", "json", "csv", "xml"]
        format_type = format_type.lower()

        if format_type not in supported_formats:
            await ctx.send(
                f"❌ Format non supporté. Formats disponibles : {', '.join(supported_formats)}"
            )
            return

        # Vérifier qu'il y a une pièce jointe
        if not ctx.message.attachments:
            await ctx.send("❌ Veuillez joindre un fichier à convertir.")
            return

        attachment = ctx.message.attachments[0]

        # Vérifier la taille du fichier (limite à 8MB)
        if attachment.size > 8 * 1024 * 1024:
            await ctx.send("❌ Le fichier est trop volumineux (limite : 8MB).")
            return

        try:
            # Télécharger le fichier
            file_content = await attachment.read()

            # Décoder le contenu (essayer UTF-8 d'abord)
            try:
                text_content = file_content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text_content = file_content.decode("latin-1")
                except UnicodeDecodeError:
                    await ctx.send(
                        "❌ Impossible de décoder le fichier. Seuls les fichiers texte sont supportés."
                    )
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
            await ctx.send(embed=embed, file=file)

        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la conversion : {str(e)}")

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
        # Vérifier la qualité
        if not 1 <= quality <= 100:
            await ctx.send("❌ La qualité doit être entre 1 et 100.")
            return

        # Vérifier qu'il y a une pièce jointe
        if not ctx.message.attachments:
            await ctx.send("❌ Veuillez joindre une image à compresser.")
            return

        attachment = ctx.message.attachments[0]

        # Vérifier que c'est une image
        if not any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
        ):
            await ctx.send("❌ Le fichier joint n'est pas une image valide.")
            return

        try:
            # Télécharger l'image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        await ctx.send("❌ Impossible de télécharger l'image.")
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
            await ctx.send(embed=embed, file=file)

        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la compression : {str(e)}")

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
        # Vérifier le nombre de couleurs
        if not 1 <= num_colors <= 40:
            await ctx.send("❌ Le nombre de couleurs doit être entre 1 et 40.")
            return

        # Vérifier qu'il y a une pièce jointe
        if not ctx.message.attachments:
            await ctx.send("❌ Veuillez joindre une image pour analyser les couleurs.")
            return

        attachment = ctx.message.attachments[0]

        # Vérifier que c'est une image
        if not any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
        ):
            await ctx.send("❌ Le fichier joint n'est pas une image valide.")
            return

        try:
            # Ajouter une réaction pour indiquer le traitement
            await ctx.message.add_reaction("⏳")

            # Télécharger l'image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        await ctx.send("❌ Impossible de télécharger l'image.")
                        return
                    image_data = await resp.read()

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

            # Créer la palette PNG (toujours générée)
            if num_colors <= 5:
                # Palette horizontale pour 5 couleurs ou moins
                palette_width = min(num_colors * 120, 600)
                palette_height = 150
                palette_img = Image.new(
                    "RGB", (palette_width, palette_height), (40, 40, 40)
                )
                draw = ImageDraw.Draw(palette_img)

                rect_width = (palette_width - 20) // num_colors
                start_x = 10

                for i, (color, percentage) in enumerate(zip(colors, percentages)):
                    x = start_x + (i * rect_width)

                    # Rectangle principal
                    draw.rectangle([x, 20, x + rect_width - 10, 130], fill=tuple(color))

                    # Bordure subtile
                    draw.rectangle(
                        [x, 20, x + rect_width - 10, 130],
                        outline=(255, 255, 255),
                        width=2,
                    )
            else:
                # Palette en grille pour plus de 5 couleurs
                cols_per_row = 5
                rows = (num_colors + cols_per_row - 1) // cols_per_row
                palette_width = cols_per_row * 120
                palette_height = rows * 100 + 50

                palette_img = Image.new(
                    "RGB", (palette_width, palette_height), (30, 30, 30)
                )
                draw = ImageDraw.Draw(palette_img)

                # Titre
                try:
                    title_font = ImageFont.truetype("arial.ttf", 20)
                except:
                    title_font = ImageFont.load_default()

                draw.text(
                    (palette_width // 2, 15),
                    f"Palette de {num_colors} couleurs",
                    fill=(255, 255, 255),
                    font=title_font,
                    anchor="mm",
                )

                # Dessiner les rectangles
                for i, (color, percentage) in enumerate(zip(colors, percentages)):
                    row = i // cols_per_row
                    col = i % cols_per_row

                    x = col * 120 + 10
                    y = row * 100 + 60

                    # Rectangle de couleur
                    draw.rectangle([x, y, x + 100, y + 80], fill=tuple(color))
                    draw.rectangle(
                        [x, y, x + 100, y + 80], outline=(255, 255, 255), width=1
                    )

                    # Numéro
                    draw.text(
                        (x + 5, y + 5),
                        str(i + 1),
                        fill=(255, 255, 255),
                        font=title_font,
                    )

            # Sauvegarder l'image de palette
            palette_output = io.BytesIO()
            palette_img.save(palette_output, format="PNG")
            palette_output.seek(0)

            # Créer le fichier texte détaillé (toujours généré)
            text_content = f"Analyse des couleurs dominantes\n"
            text_content += f"Image: {attachment.filename}\n"
            text_content += f"Résolution: {original_size[0]}x{original_size[1]}px\n"
            text_content += f"Nombre de couleurs analysées: {num_colors}\n"
            text_content += f"Généré par: {ctx.author.display_name}\n"
            text_content += (
                f"Serveur: {ctx.guild.name if ctx.guild else 'Message privé'}\n\n"
            )
            text_content += "Couleurs par ordre de dominance:\n"
            text_content += "=" * 60 + "\n\n"

            embed_color_info = []

            for i, (color, percentage) in enumerate(zip(colors, percentages)):
                # Convertir en hex
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

                # Ajouter au fichier texte détaillé
                text_content += f"{i+1:2d}. {hex_color.upper()} - {percentage:.2f}%\n"
                text_content += (
                    f"    RGB({color[0]:3d}, {color[1]:3d}, {color[2]:3d})\n"
                )
                text_content += f"    HSV({self._rgb_to_hsv(color)})\n"
                text_content += f"    Luminosité: {(0.299*color[0] + 0.587*color[1] + 0.114*color[2]):.1f}\n"
                text_content += "-" * 40 + "\n\n"

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

                if num_colors <= 5:
                    embed_color_info.append(
                        f"{emoji} **{percentage:.1f}%** - `{hex_color}`\n└ RGB({color[0]}, {color[1]}, {color[2]})"
                    )

            # Créer le fichier texte
            text_output = io.BytesIO(text_content.encode("utf-8"))

            # Créer l'embed
            if num_colors <= 5:
                embed = self.create_embed(
                    f"🎨 Palette de {num_colors} couleur(s) dominante(s)",
                    f"**Image :** {attachment.filename}\n**Résolution :** {original_size[0]}x{original_size[1]}px\n\n"
                    + "\n\n".join(embed_color_info)
                    + f"\n\n⬇️ **Fichiers générés :**\n• `palette_couleurs.png` - Palette visuelle\n• `couleurs_detaillees.txt` - Données complètes",
                )
                embed.set_thumbnail(url=attachment.url)
                embed.set_image(url="attachment://palette_couleurs.png")
            else:
                embed = self.create_embed(
                    f"🎨 Analyse complète de {num_colors} couleurs",
                    f"**Image :** {attachment.filename}\n**Résolution :** {original_size[0]}x{original_size[1]}px\n\n⬇️ **Fichiers générés :**\n• `palette_complete.png` - Palette visuelle\n• `couleurs_detaillees.txt` - Données complètes",
                )
                embed.set_thumbnail(url=attachment.url)

            # Toujours envoyer les deux fichiers
            files = [
                discord.File(
                    palette_output,
                    filename=(
                        "palette_couleurs.png"
                        if num_colors <= 5
                        else "palette_complete.png"
                    ),
                ),
                discord.File(text_output, filename="couleurs_detaillees.txt"),
            ]

            await ctx.message.remove_reaction("⏳", ctx.bot.user)
            await ctx.send(embed=embed, files=files)

        except Exception as e:
            await ctx.message.remove_reaction("⏳", ctx.bot.user)
            await ctx.send(f"❌ Erreur lors de l'analyse des couleurs : {str(e)}")

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
        # Vérifier le facteur d'agrandissement
        if not 1.5 <= scale_factor <= 4.0:
            await ctx.send("❌ Le facteur doit être entre 1.5 et 4.0.")
            return

        # Vérifier qu'il y a une pièce jointe
        if not ctx.message.attachments:
            await ctx.send("❌ Veuillez joindre une image à améliorer.")
            return

        attachment = ctx.message.attachments[0]

        # Vérifier que c'est une image
        if not any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
        ):
            await ctx.send("❌ Le fichier joint n'est pas une image valide.")
            return

        # Vérifier la taille du fichier (limite plus stricte pour l'amélioration)
        if attachment.size > 5 * 1024 * 1024:  # 5MB max
            await ctx.send(
                "❌ L'image est trop volumineuse pour l'amélioration (limite : 5MB)."
            )
            return

        try:
            # Ajouter une réaction pour indiquer le traitement
            await ctx.message.add_reaction("⏳")

            # Télécharger l'image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        await ctx.send("❌ Impossible de télécharger l'image.")
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
                await ctx.send(
                    "❌ La résolution finale serait trop importante. Réduisez le facteur d'agrandissement."
                )
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

            await ctx.message.remove_reaction("⏳", ctx.bot.user)
            await ctx.send(embed=embed, file=file)

        except Exception as e:
            await ctx.message.remove_reaction("⏳", ctx.bot.user)
            await ctx.send(f"❌ Erreur lors de l'amélioration : {str(e)}")

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
