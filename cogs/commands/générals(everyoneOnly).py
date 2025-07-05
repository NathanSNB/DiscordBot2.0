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

    def create_embed(self, title, description=None, color=None):
        """Crée un embed standard"""
        if color is None:
            color = EmbedManager.get_default_color()
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Bot Discord - Commandes Générales")
        return embed

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
        print(f'Cog ProfilePicture connecté en tant que {self.bot.user}')
    
    @commands.command(
        name="pic",
        help="Affiche une photo de profil",
        description="Affiche la photo de profil d'un utilisateur en haute résolution",
        usage="[@utilisateur]"
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
        usage="<nombre1> <opérateur> <nombre2>"
    )
    async def calc(self, ctx, a: float, operation: str, b: float):
        try:
            if operation not in ['+', '-', '*', '/']:
                await ctx.send("❌ Opération invalide. Utilisez : +, -, *, /")
                return
                
            if operation == '/' and b == 0:
                await ctx.send("❌ Division par zéro impossible")
                return

            operations = {
                '+': lambda x, y: x + y,
                '-': lambda x, y: x - y,
                '*': lambda x, y: x * y,
                '/': lambda x, y: x / y
            }
            
            result = operations[operation](a, b)
            embed = self.create_embed(
                "🔢 Calculatrice",
                f"{a} {operation} {b} = {result:.2f}"
            )
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("❌ Veuillez entrer des nombres valides")

    @commands.command(
        name="roll",
        help="Lance un dé",
        description="Génère un nombre aléatoire entre 1 et 10",
        usage=""
    )
    async def roll(self, ctx):
        result = random.randint(1, 10)
        embed = self.create_embed(
            "🎲 Jet de dé",
            f"{ctx.author.mention} a obtenu : **{result}**"
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="say",
        help="Répète un message",
        description="Répète un message dans un salon spécifique un certain nombre de fois",
        usage="<message> [#salon] [nombre]"
    )
    async def say(self, ctx, *, args):
        """Répète un message dans un salon"""
        try:
            # Extraction des arguments
            parts = args.split()
            
            # Vérification du salon
            if len(parts) >= 2 and parts[-2].startswith('<#') and parts[-2].endswith('>'):
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
            message = ' '.join(parts)
            
            # Envoi des messages
            for _ in range(count):
                await channel.send(message)
                await asyncio.sleep(1)
            
            embed = self.create_embed(
                "📢 Message répété",
                f"Message envoyé {count} fois dans {channel.mention}"
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission d'envoyer des messages dans ce salon")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

    @commands.command(
        name="iconvert",
        help="Convertit une image - Formats: png, jpg, jpeg, webp, gif, bmp",
        description="Convertit une image jointe vers le format spécifié. Formats supportés: png, jpg, jpeg, webp, gif, bmp",
        usage="<format> (avec image en pièce jointe)"
    )
    async def iconvert(self, ctx, format_type: str):
        """Convertit une image vers le format spécifié
        Usage: +iconvert <format> (avec image en pièce jointe)
        Formats supportés: png, jpg, jpeg, webp, gif, bmp
        """
        # Formats d'image supportés
        supported_formats = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp']
        format_type = format_type.lower()
        
        if format_type not in supported_formats:
            await ctx.send(f"❌ Format non supporté. Formats disponibles : {', '.join(supported_formats)}")
            return
        
        # Vérifier qu'il y a une pièce jointe
        if not ctx.message.attachments:
            await ctx.send("❌ Veuillez joindre une image à convertir.")
            return
        
        attachment = ctx.message.attachments[0]
        
        # Vérifier que c'est une image
        if not any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
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
            if format_type in ['jpg', 'jpeg'] and image.mode in ['RGBA', 'P']:
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Sauvegarder dans le nouveau format
            output = io.BytesIO()
            if format_type == 'jpg':
                format_type = 'jpeg'
            image.save(output, format=format_type.upper())
            output.seek(0)
            
            # Créer le nom du fichier de sortie
            original_name = attachment.filename.rsplit('.', 1)[0]
            new_filename = f"{original_name}_converted.{format_type}"
            
            # Envoyer le fichier converti
            file = discord.File(output, filename=new_filename)
            embed = self.create_embed(
                "🖼️ Conversion d'image réussie",
                f"Image convertie en format {format_type.upper()}"
            )
            await ctx.send(embed=embed, file=file)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la conversion : {str(e)}")

    @commands.command(
        name="fconvert",
        help="Convertit un fichier - Formats: txt, md, html, json, csv, xml",
        description="Convertit un fichier texte vers le format spécifié. Formats supportés: txt, md, html, json, csv, xml",
        usage="<format> (avec fichier en pièce jointe)"
    )
    async def fconvert(self, ctx, format_type: str):
        """Convertit un fichier texte vers le format spécifié
        Usage: +fconvert <format> (avec fichier en pièce jointe)
        Formats supportés: txt, md, html, json, csv, xml
        """
        # Formats de fichier supportés (principalement texte)
        supported_formats = ['txt', 'md', 'html', 'json', 'csv', 'xml']
        format_type = format_type.lower()
        
        if format_type not in supported_formats:
            await ctx.send(f"❌ Format non supporté. Formats disponibles : {', '.join(supported_formats)}")
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
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = file_content.decode('latin-1')
                except UnicodeDecodeError:
                    await ctx.send("❌ Impossible de décoder le fichier. Seuls les fichiers texte sont supportés.")
                    return
            
            # Convertir selon le format demandé
            if format_type == 'html':
                # Conversion simple texte vers HTML
                converted_content = f"<!DOCTYPE html>\n<html>\n<head>\n<title>Fichier converti</title>\n</head>\n<body>\n<pre>{text_content}</pre>\n</body>\n</html>"
            elif format_type == 'md':
                # Conversion vers Markdown (ajouter des backticks pour le code)
                converted_content = f"# Fichier converti\n\n```\n{text_content}\n```"
            elif format_type == 'xml':
                # Conversion simple vers XML
                converted_content = f"<?xml version='1.0' encoding='UTF-8'?>\n<document>\n<content><![CDATA[{text_content}]]></content>\n</document>"
            else:
                # Pour txt, json, csv - garder le contenu tel quel
                converted_content = text_content
            
            # Créer le nom du fichier de sortie
            original_name = attachment.filename.rsplit('.', 1)[0]
            new_filename = f"{original_name}_converted.{format_type}"
            
            # Créer le fichier de sortie
            output = io.BytesIO(converted_content.encode('utf-8'))
            file = discord.File(output, filename=new_filename)
            
            embed = self.create_embed(
                "📄 Conversion de fichier réussie",
                f"Fichier converti en format {format_type.upper()}"
            )
            await ctx.send(embed=embed, file=file)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la conversion : {str(e)}")

    @commands.command(
        name="compress",
        help="Compresse une image - Réduit la taille et qualité",
        description="Compresse une image jointe pour réduire sa taille de fichier",
        usage="[qualité] (avec image en pièce jointe)"
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
        if not any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
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
            if image.mode in ['RGBA', 'P']:
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Compresser l'image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            compressed_size = len(output.getvalue())
            compression_ratio = round((1 - compressed_size / original_size) * 100, 1)
            
            # Créer le nom du fichier de sortie
            original_name = attachment.filename.rsplit('.', 1)[0]
            new_filename = f"{original_name}_compressed.jpg"
            
            # Envoyer le fichier compressé
            file = discord.File(output, filename=new_filename)
            embed = self.create_embed(
                "🗜️ Compression d'image réussie",
                f"Taille originale: {original_size // 1024} KB\nTaille compressée: {compressed_size // 1024} KB\nRéduction: {compression_ratio}%\nQualité: {quality}%"
            )
            await ctx.send(embed=embed, file=file)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la compression : {str(e)}")

    @commands.command(
        name="bgcolor",
        help="Extrait les couleurs dominantes - Usage: !bgcolor <nombre>",
        description="Extrait les couleurs dominantes d'une image jointe avec palette visuelle",
        usage="<nombre> (avec image en pièce jointe)"
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
        if not any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
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
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
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
                palette_img = Image.new('RGB', (palette_width, palette_height), (40, 40, 40))
                draw = ImageDraw.Draw(palette_img)
                
                rect_width = (palette_width - 20) // num_colors
                start_x = 10
                
                for i, (color, percentage) in enumerate(zip(colors, percentages)):
                    x = start_x + (i * rect_width)
                    
                    # Rectangle principal
                    draw.rectangle([x, 20, x + rect_width - 10, 130], fill=tuple(color))
                    
                    # Bordure subtile
                    draw.rectangle([x, 20, x + rect_width - 10, 130], outline=(255, 255, 255), width=2)
            else:
                # Palette en grille pour plus de 5 couleurs
                cols_per_row = 5
                rows = (num_colors + cols_per_row - 1) // cols_per_row
                palette_width = cols_per_row * 120
                palette_height = rows * 100 + 50
                
                palette_img = Image.new('RGB', (palette_width, palette_height), (30, 30, 30))
                draw = ImageDraw.Draw(palette_img)
                
                # Titre
                try:
                    title_font = ImageFont.truetype("arial.ttf", 20)
                except:
                    title_font = ImageFont.load_default()
                
                draw.text((palette_width//2, 15), f"Palette de {num_colors} couleurs", 
                         fill=(255, 255, 255), font=title_font, anchor="mm")
                
                # Dessiner les rectangles
                for i, (color, percentage) in enumerate(zip(colors, percentages)):
                    row = i // cols_per_row
                    col = i % cols_per_row
                    
                    x = col * 120 + 10
                    y = row * 100 + 60
                    
                    # Rectangle de couleur
                    draw.rectangle([x, y, x + 100, y + 80], fill=tuple(color))
                    draw.rectangle([x, y, x + 100, y + 80], outline=(255, 255, 255), width=1)
                    
                    # Numéro
                    draw.text((x + 5, y + 5), str(i + 1), fill=(255, 255, 255), font=title_font)
            
            # Sauvegarder l'image de palette
            palette_output = io.BytesIO()
            palette_img.save(palette_output, format='PNG')
            palette_output.seek(0)
            
            # Créer le fichier texte détaillé (toujours généré)
            text_content = f"Analyse des couleurs dominantes\n"
            text_content += f"Image: {attachment.filename}\n"
            text_content += f"Résolution: {original_size[0]}x{original_size[1]}px\n"
            text_content += f"Nombre de couleurs analysées: {num_colors}\n"
            text_content += f"Généré par: {ctx.author.display_name}\n"
            text_content += f"Serveur: {ctx.guild.name if ctx.guild else 'Message privé'}\n\n"
            text_content += "Couleurs par ordre de dominance:\n"
            text_content += "=" * 60 + "\n\n"
            
            embed_color_info = []
            
            for i, (color, percentage) in enumerate(zip(colors, percentages)):
                # Convertir en hex
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                
                # Ajouter au fichier texte détaillé
                text_content += f"{i+1:2d}. {hex_color.upper()} - {percentage:.2f}%\n"
                text_content += f"    RGB({color[0]:3d}, {color[1]:3d}, {color[2]:3d})\n"
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
                    embed_color_info.append(f"{emoji} **{percentage:.1f}%** - `{hex_color}`\n└ RGB({color[0]}, {color[1]}, {color[2]})")
            
            # Créer le fichier texte
            text_output = io.BytesIO(text_content.encode('utf-8'))
            
            # Créer l'embed
            if num_colors <= 5:
                embed = self.create_embed(
                    f"🎨 Palette de {num_colors} couleur(s) dominante(s)",
                    f"**Image :** {attachment.filename}\n**Résolution :** {original_size[0]}x{original_size[1]}px\n\n" + "\n\n".join(embed_color_info) + f"\n\n⬇️ **Fichiers générés :**\n• `palette_couleurs.png` - Palette visuelle\n• `couleurs_detaillees.txt` - Données complètes"
                )
                embed.set_thumbnail(url=attachment.url)
                embed.set_image(url="attachment://palette_couleurs.png")
            else:
                embed = self.create_embed(
                    f"🎨 Analyse complète de {num_colors} couleurs",
                    f"**Image :** {attachment.filename}\n**Résolution :** {original_size[0]}x{original_size[1]}px\n\n⬇️ **Fichiers générés :**\n• `palette_complete.png` - Palette visuelle\n• `couleurs_detaillees.txt` - Données complètes"
                )
                embed.set_thumbnail(url=attachment.url)
            
            # Toujours envoyer les deux fichiers
            files = [
                discord.File(palette_output, filename="palette_couleurs.png" if num_colors <= 5 else "palette_complete.png"),
                discord.File(text_output, filename="couleurs_detaillees.txt")
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
        usage="[facteur] (avec image en pièce jointe)"
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
        if not any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
            await ctx.send("❌ Le fichier joint n'est pas une image valide.")
            return
        
        # Vérifier la taille du fichier (limite plus stricte pour l'amélioration)
        if attachment.size > 5 * 1024 * 1024:  # 5MB max
            await ctx.send("❌ L'image est trop volumineuse pour l'amélioration (limite : 5MB).")
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
            if image.mode in ['RGBA']:
                # Conserver la transparence pour PNG
                pass
            elif image.mode in ['P']:
                image = image.convert('RGBA')
            elif image.mode not in ['RGB', 'RGBA']:
                image = image.convert('RGB')
            
            # Calculer la nouvelle taille
            new_width = int(original_resolution[0] * scale_factor)
            new_height = int(original_resolution[1] * scale_factor)
            
            # Vérifier que la nouvelle résolution n'est pas trop grande
            if new_width * new_height > 16000000:  # ~16 mégapixels max
                await ctx.send("❌ La résolution finale serait trop importante. Réduisez le facteur d'agrandissement.")
                return
            
            # Améliorer l'image avec différentes techniques
            
            # 1. Redimensionnement avec algorithme Lanczos (haute qualité)
            enhanced_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 2. Appliquer des filtres d'amélioration
            from PIL import ImageEnhance, ImageFilter
            
            # Améliorer la netteté
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced_image)
            enhanced_image = sharpness_enhancer.enhance(1.2)  # Augmenter légèrement la netteté
            
            # Améliorer le contraste légèrement
            contrast_enhancer = ImageEnhance.Contrast(enhanced_image)
            enhanced_image = contrast_enhancer.enhance(1.1)
            
            # Appliquer un filtre de netteté supplémentaire pour les détails
            if scale_factor >= 2.0:
                enhanced_image = enhanced_image.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            # Sauvegarder l'image améliorée
            output = io.BytesIO()
            
            # Choisir le format et la qualité de sortie
            original_format = image.format or 'PNG'
            if original_format.upper() == 'JPEG' or attachment.filename.lower().endswith(('.jpg', '.jpeg')):
                enhanced_image = enhanced_image.convert('RGB')  # JPEG ne supporte pas la transparence
                enhanced_image.save(output, format='JPEG', quality=95, optimize=True)
                file_extension = 'jpg'
            else:
                enhanced_image.save(output, format='PNG', optimize=True)
                file_extension = 'png'
            
            output.seek(0)
            enhanced_size_bytes = len(output.getvalue())
            
            # Calculer les statistiques
            resolution_increase = ((new_width * new_height) / (original_resolution[0] * original_resolution[1]) - 1) * 100
            size_change = ((enhanced_size_bytes / original_size_bytes) - 1) * 100
            
            # Créer le nom du fichier de sortie
            original_name = attachment.filename.rsplit('.', 1)[0]
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
                f"**Améliorations appliquées:** Redimensionnement Lanczos, netteté, contraste"
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

    @commands.command(
        name="font",
        help="Transforme le texte en plusieurs styles de police",
        description="Affiche le texte fourni avec différents styles de police Unicode (gras, italique, monospace, etc.)",
        usage="<texte>"
    )
    async def font(self, ctx, *, text: str):
        """Transforme le texte en plusieurs styles de police Unicode
        Usage: !font <texte>
        """
        if not text:
            await ctx.send("❌ Veuillez fournir du texte à transformer.")
            return
        
        if len(text) > 100:
            await ctx.send("❌ Le texte est trop long (limite: 100 caractères).")
            return
        
        try:
            # Dictionnaires de transformation Unicode
            styles = {
                "Bold": self._transform_bold(text),
                "Italic": self._transform_italic(text),
                "Bold Italic": self._transform_bold_italic(text),
                "Monospace": self._transform_monospace(text),
                "Sans-serif": self._transform_sans_serif(text),
                "Sans-serif Bold": self._transform_sans_serif_bold(text),
                "Sans-serif Italic": self._transform_sans_serif_italic(text),
                "Double-struck": self._transform_double_struck(text),
                "Script": self._transform_script(text),
                "Fraktur": self._transform_fraktur(text)
            }
            
            # Créer l'embed avec tous les styles
            embed = self.create_embed(
                "🎨 Styles de police",
                f"**Texte original:** {text}\n\n"
            )
            
            for style_name, transformed_text in styles.items():
                embed.add_field(
                    name=f"**{style_name}**",
                    value=transformed_text,
                    inline=False
                )
            
            embed.set_footer(text="Utilise les caractères Unicode pour les transformations")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la transformation du texte : {str(e)}")

    def _transform_bold(self, text):
        """Transforme le texte en gras Unicode"""
        bold_map = {
            'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇', 'I': '𝐈', 'J': '𝐉',
            'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓',
            'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
            'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠', 'h': '𝐡', 'i': '𝐢', 'j': '𝐣',
            'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭',
            'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳',
            '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
        }
        return ''.join(bold_map.get(char, char) for char in text)

    def _transform_italic(self, text):
        """Transforme le texte en italique Unicode"""
        italic_map = {
            'A': '𝐴', 'B': '𝐵', 'C': '𝐶', 'D': '𝐷', 'E': '𝐸', 'F': '𝐹', 'G': '𝐺', 'H': '𝐻', 'I': '𝐼', 'J': '𝐽',
            'K': '𝐾', 'L': '𝐿', 'M': '𝑀', 'N': '𝑁', 'O': '𝑂', 'P': '𝑃', 'Q': '𝑄', 'R': '𝑅', 'S': '𝑆', 'T': '𝑇',
            'U': '𝑈', 'V': '𝑉', 'W': '𝑊', 'X': '𝑋', 'Y': '𝑌', 'Z': '𝑍',
            'a': '𝑎', 'b': '𝑏', 'c': '𝑐', 'd': '𝑑', 'e': '𝑒', 'f': '𝑓', 'g': '𝑔', 'h': 'ℎ', 'i': '𝑖', 'j': '𝑗',
            'k': '𝑘', 'l': '𝑙', 'm': '𝑚', 'n': '𝑛', 'o': '𝑜', 'p': '𝑝', 'q': '𝑞', 'r': '𝑟', 's': '𝑠', 't': '𝑡',
            'u': '𝑢', 'v': '𝑣', 'w': '𝑤', 'x': '𝑥', 'y': '𝑦', 'z': '𝑧'
        }
        return ''.join(italic_map.get(char, char) for char in text)

    def _transform_bold_italic(self, text):
        """Transforme le texte en gras italique Unicode"""
        bold_italic_map = {
            'A': '𝑨', 'B': '𝑩', 'C': '𝑪', 'D': '𝑫', 'E': '𝑬', 'F': '𝑭', 'G': '𝑮', 'H': '𝑯', 'I': '𝑰', 'J': '𝑱',
            'K': '𝑲', 'L': '𝑳', 'M': '𝑴', 'N': '𝑵', 'O': '𝑶', 'P': '𝑷', 'Q': '𝑸', 'R': '𝑹', 'S': '𝑺', 'T': '𝑻',
            'U': '𝑼', 'V': '𝑽', 'W': '𝑾', 'X': '𝑿', 'Y': '𝒀', 'Z': '𝒁',
            'a': '𝒂', 'b': '𝒃', 'c': '𝒄', 'd': '𝒅', 'e': '𝒆', 'f': '𝒇', 'g': '𝒈', 'h': '𝒉', 'i': '𝒊', 'j': '𝒋',
            'k': '𝒌', 'l': '𝒍', 'm': '𝒎', 'n': '𝒏', 'o': '𝒐', 'p': '𝒑', 'q': '𝒒', 'r': '𝒓', 's': '𝒔', 't': '𝒕',
            'u': '𝒖', 'v': '𝒗', 'w': '𝒘', 'x': '𝒙', 'y': '𝒚', 'z': '𝒛'
        }
        return ''.join(bold_italic_map.get(char, char) for char in text)

    def _transform_monospace(self, text):
        """Transforme le texte en monospace Unicode"""
        monospace_map = {
            'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸', 'J': '𝙹',
            'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁', 'S': '𝚂', 'T': '𝚃',
            'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
            'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒', 'j': '𝚓',
            'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛', 's': '𝚜', 't': '𝚝',
            'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
            '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿'
        }
        return ''.join(monospace_map.get(char, char) for char in text)

    def _transform_sans_serif(self, text):
        """Transforme le texte en sans-serif Unicode"""
        sans_serif_map = {
            'A': '𝖠', 'B': '𝖡', 'C': '𝖢', 'D': '𝖣', 'E': '𝖤', 'F': '𝖥', 'G': '𝖦', 'H': '𝖧', 'I': '𝖨', 'J': '𝖩',
            'K': '𝖪', 'L': '𝖫', 'M': '𝖬', 'N': '𝖭', 'O': '𝖮', 'P': '𝖯', 'Q': '𝖰', 'R': '𝖱', 'S': '𝖲', 'T': '𝖳',
            'U': '𝖴', 'V': '𝖵', 'W': '𝖶', 'X': '𝖷', 'Y': '𝖸', 'Z': '𝖹',
            'a': '𝖺', 'b': '𝖻', 'c': '𝖼', 'd': '𝖽', 'e': '𝖾', 'f': '𝖿', 'g': '𝗀', 'h': '𝗁', 'i': '𝗂', 'j': '𝗃',
            'k': '𝗄', 'l': '𝗅', 'm': '𝗆', 'n': '𝗇', 'o': '𝗈', 'p': '𝗉', 'q': '𝗊', 'r': '𝗋', 's': '𝗌', 't': '𝗍',
            'u': '𝗎', 'v': '𝗏', 'w': '𝗐', 'x': '𝗑', 'y': '𝗒', 'z': '𝗓',
            '0': '𝟢', '1': '𝟣', '2': '𝟤', '3': '𝟥', '4': '𝟦', '5': '𝟧', '6': '𝟨', '7': '𝟩', '8': '𝟪', '9': '𝟫'
        }
        return ''.join(sans_serif_map.get(char, char) for char in text)

    def _transform_sans_serif_bold(self, text):
        """Transforme le texte en sans-serif gras Unicode"""
        sans_serif_bold_map = {
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝',
            'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧',
            'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
            'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷',
            'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁',
            'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
            '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
        }
        return ''.join(sans_serif_bold_map.get(char, char) for char in text)

    def _transform_sans_serif_italic(self, text):
        """Transforme le texte en sans-serif italique Unicode"""
        sans_serif_italic_map = {
            'A': '𝘈', 'B': '𝘉', 'C': '𝘊', 'D': '𝘋', 'E': '𝘌', 'F': '𝘍', 'G': '𝘎', 'H': '𝘏', 'I': '𝘐', 'J': '𝘑',
            'K': '𝘒', 'L': '𝘓', 'M': '𝘔', 'N': '𝘕', 'O': '𝘖', 'P': '𝘗', 'Q': '𝘘', 'R': '𝘙', 'S': '𝘚', 'T': '𝘛',
            'U': '𝘜', 'V': '𝘝', 'W': '𝘞', 'X': '𝘟', 'Y': '𝘠', 'Z': '𝘡',
            'a': '𝘢', 'b': '𝘣', 'c': '𝘤', 'd': '𝘥', 'e': '𝘦', 'f': '𝘧', 'g': '𝘨', 'h': '𝘩', 'i': '𝘪', 'j': '𝘫',
            'k': '𝘬', 'l': '𝘭', 'm': '𝘮', 'n': '𝘯', 'o': '𝘰', 'p': '𝘱', 'q': '𝘲', 'r': '𝘳', 's': '𝘴', 't': '𝘵',
            'u': '𝘶', 'v': '𝘷', 'w': '𝘸', 'x': '𝘹', 'y': '𝘺', 'z': '𝘻'
        }
        return ''.join(sans_serif_italic_map.get(char, char) for char in text)

    def _transform_double_struck(self, text):
        """Transforme le texte en double-struck Unicode"""
        double_struck_map = {
            'A': '𝔸', 'B': '𝔹', 'C': 'ℂ', 'D': '𝔻', 'E': '𝔼', 'F': '𝔽', 'G': '𝔾', 'H': 'ℍ', 'I': '𝕀', 'J': '𝕁',
            'K': '𝕂', 'L': '𝕃', 'M': '𝕄', 'N': 'ℕ', 'O': '𝕆', 'P': 'ℙ', 'Q': 'ℚ', 'R': 'ℝ', 'S': '𝕊', 'T': '𝕋',
            'U': '𝕌', 'V': '𝕍', 'W': '𝕎', 'X': '𝕏', 'Y': '𝕐', 'Z': 'ℤ',
            'a': '𝕒', 'b': '𝕓', 'c': '𝕔', 'd': '𝕕', 'e': '𝕖', 'f': '𝕗', 'g': '𝕘', 'h': '𝕙', 'i': '𝕚', 'j': '𝕛',
            'k': '𝕜', 'l': '𝕝', 'm': '𝕞', 'n': '𝕟', 'o': '𝕠', 'p': '𝕡', 'q': '𝕢', 'r': '𝕣', 's': '𝕤', 't': '𝕥',
            'u': '𝕦', 'v': '𝕧', 'w': '𝕨', 'x': '𝕩', 'y': '𝕪', 'z': '𝕫',
            '0': '𝟘', '1': '𝟙', '2': '𝟚', '3': '𝟛', '4': '𝟜', '5': '𝟝', '6': '𝟞', '7': '𝟟', '8': '𝟠', '9': '𝟡'
        }
        return ''.join(double_struck_map.get(char, char) for char in text)

    def _transform_script(self, text):
        """Transforme le texte en script Unicode"""
        script_map = {
            'A': '𝒜', 'B': 'ℬ', 'C': '𝒞', 'D': '𝒟', 'E': 'ℰ', 'F': 'ℱ', 'G': '𝒢', 'H': 'ℋ', 'I': 'ℐ', 'J': '𝒥',
            'K': '𝒦', 'L': 'ℒ', 'M': 'ℳ', 'N': '𝒩', 'O': '𝒪', 'P': '𝒫', 'Q': '𝒬', 'R': 'ℛ', 'S': '𝒮', 'T': '𝒯',
            'U': '𝒰', 'V': '𝒱', 'W': '𝒲', 'X': '𝒳', 'Y': '𝒴', 'Z': '𝒵',
            'a': '𝒶', 'b': '𝒷', 'c': '𝒸', 'd': '𝒹', 'e': 'ℯ', 'f': '𝒻', 'g': 'ℊ', 'h': '𝒽', 'i': '𝒾', 'j': '𝒿',
            'k': '𝓀', 'l': '𝓁', 'm': '𝓂', 'n': '𝓃', 'o': 'ℴ', 'p': '𝓅', 'q': '𝓆', 'r': '𝓇', 's': '𝓈', 't': '𝓉',
            'u': '𝓊', 'v': '𝓋', 'w': '𝓌', 'x': '𝓍', 'y': '𝓎', 'z': '𝓏'
        }
        return ''.join(script_map.get(char, char) for char in text)

    def _transform_fraktur(self, text):
        """Transforme le texte en fraktur Unicode"""
        fraktur_map = {
            'A': '𝔄', 'B': '𝔅', 'C': 'ℭ', 'D': '𝔇', 'E': '𝔈', 'F': '𝔉', 'G': '𝔊', 'H': 'ℌ', 'I': 'ℑ', 'J': '𝔍',
            'K': '𝔎', 'L': '𝔏', 'M': '𝔐', 'N': '𝔑', 'O': '𝔒', 'P': '𝔓', 'Q': '𝔔', 'R': 'ℜ', 'S': '𝔖', 'T': '𝔗',
            'U': '𝔘', 'V': '𝔙', 'W': '𝔚', 'X': '𝔛', 'Y': '𝔜', 'Z': 'ℨ',
            'a': '𝔞', 'b': '𝔟', 'c': '𝔠', 'd': '𝔡', 'e': '𝔢', 'f': '𝔣', 'g': '𝔤', 'h': '𝔥', 'i': '𝔦', 'j': '𝔧',
            'k': '𝔨', 'l': '𝔩', 'm': '𝔪', 'n': '𝔫', 'o': '𝔬', 'p': '𝔭', 'q': '𝔮', 'r': '𝔯', 's': '𝔰', 't': '𝔱',
            'u': '𝔲', 'v': '𝔳', 'w': '𝔴', 'x': '𝔵', 'y': '𝔶', 'z': '𝔷'
        }
        return ''.join(fraktur_map.get(char, char) for char in text)

async def setup(bot):
    await bot.add_cog(CommandesGénérales(bot))
