import discord
from discord import app_commands
from discord.ext import commands
import requests
import qrcode
from io import BytesIO
import aiohttp
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from utils.embed_manager import EmbedManager
from utils.error import ErrorHandler


class Commandes_Webs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()
        self.BITLY_API_KEY = os.getenv("BITLY_API_KEY")
        self.VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

        if not self.BITLY_API_KEY or not self.VIRUSTOTAL_API_KEY:
            print("⚠️ Les clés API ne sont pas définies dans le fichier .env")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Gestion globale des erreurs"""
        await ErrorHandler.handle_command_error(ctx, error)

    def create_embed(self, title, description=None, embed_type="tools"):
        """Crée un embed standard pour les utilitaires"""
        return EmbedManager.create_professional_embed(
            title=title,
            description=description,
            embed_type=embed_type
        )

    def is_valid_url(self, url):
        """Vérifie si l'URL est valide (http:// ou https://)."""
        try:
            result = urlparse(url)
            return result.scheme in ["http", "https"] and result.netloc
        except ValueError:
            return False

    @commands.command(
        name="shorten",
        help="Raccourcit une URL",
        description="Utilise l'API Bitly pour raccourcir une URL longue",
        usage="<url>",
    )
    async def shorten_url(self, ctx, url: str):
        if not self.BITLY_API_KEY:
            await ctx.send("Erreur : la clé API Bitly n'est pas configurée.")
            return

        if not self.is_valid_url(url):
            await ctx.send(
                "❌ URL invalide. L'URL doit commencer par http:// ou https://"
            )
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.BITLY_API_KEY}",
                "Content-Type": "application/json",
            }
            response = requests.post(
                "https://api-ssl.bitly.com/v4/shorten",
                headers=headers,
                json={"long_url": url},
            )

            if response.status_code == 200:
                short_url = response.json().get("link")
                embed = self.create_embed(
                    "🔗 URL Raccourcie",
                    f"URL d'origine : {url}\nURL courte : {short_url}",
                )
                await ctx.send(embed=embed)
            else:
                error_msg = response.json().get("message", "Erreur inconnue")
                await ctx.send(
                    f"❌ Erreur lors du raccourcissement de l’URL : {error_msg}"
                )
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

    @app_commands.command(name="shorten", description="Raccourcit une URL longue")
    @app_commands.describe(url="URL à raccourcir (doit commencer par http:// ou https://)")
    async def shorten_slash(self, interaction: discord.Interaction, url: str):
        """Version slash command pour raccourcir une URL"""
        if not self.BITLY_API_KEY:
            await interaction.response.send_message("Erreur : la clé API Bitly n'est pas configurée.", ephemeral=True)
            return

        if not self.is_valid_url(url):
            await interaction.response.send_message(
                "❌ URL invalide. L'URL doit commencer par http:// ou https://", ephemeral=True
            )
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.BITLY_API_KEY}",
                "Content-Type": "application/json",
            }
            response = requests.post(
                "https://api-ssl.bitly.com/v4/shorten",
                headers=headers,
                json={"long_url": url},
            )

            if response.status_code == 200:
                short_url = response.json().get("link")
                embed = self.create_embed(
                    "🔗 URL Raccourcie",
                    f"URL d'origine : {url}\nURL courte : {short_url}",
                )
                await interaction.response.send_message(embed=embed)
            else:
                error_msg = response.json().get("message", "Erreur inconnue")
                await interaction.response.send_message(
                    f"❌ Erreur lors du raccourcissement de l'URL : {error_msg}", ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(f"❌ Une erreur est survenue : {str(e)}", ephemeral=True)

    @commands.command(
        name="qrcode",
        help="Génère un QR Code",
        description="Crée un QR Code à partir d'une URL",
        usage="<url>",
    )
    async def generate_qrcode(self, ctx, url: str):
        if not self.is_valid_url(url):
            await ctx.send(
                "❌ URL invalide. L'URL doit commencer par http:// ou https://"
            )
            return

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            embed = self.create_embed("📱 QR Code généré", f"URL encodée : {url}")
            await ctx.send(
                embed=embed, file=discord.File(buffer, filename="qrcode.png")
            )
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

    @app_commands.command(name="qrcode", description="Génère un QR Code à partir d'une URL")
    @app_commands.describe(url="URL à encoder en QR Code (doit commencer par http:// ou https://)")
    async def qrcode_slash(self, interaction: discord.Interaction, url: str):
        """Version slash command pour générer un QR Code"""
        if not self.is_valid_url(url):
            await interaction.response.send_message(
                "❌ URL invalide. L'URL doit commencer par http:// ou https://", ephemeral=True
            )
            return

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            embed = self.create_embed("📱 QR Code généré", f"URL encodée : {url}")
            await interaction.response.send_message(
                embed=embed, file=discord.File(buffer, filename="qrcode.png")
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Une erreur est survenue : {str(e)}", ephemeral=True)

    @commands.command(
        name="scan",
        help="Analyse une URL",
        description="Vérifie si une URL est potentiellement malveillante via VirusTotal",
        usage="<url>",
    )
    async def scan_url(self, ctx, url: str):
        if not self.VIRUSTOTAL_API_KEY:
            await ctx.send("Erreur : la clé API VirusTotal n'est pas configurée.")
            return

        if not self.is_valid_url(url):
            await ctx.send(
                "❌ URL invalide. L'URL doit commencer par http:// ou https://"
            )
            return

        status_msg = await ctx.send("🔎 Analyse en cours...")
        try:
            headers = {"x-apikey": self.VIRUSTOTAL_API_KEY}
            async with aiohttp.ClientSession() as session:
                # Soumet l'URL pour analyse
                async with session.post(
                    "https://www.virustotal.com/api/v3/urls",
                    headers=headers,
                    data={"url": url},
                ) as response:
                    if response.status != 200:
                        await status_msg.edit(content="❌ Erreur lors de l'analyse")
                        return

                    result = await response.json()
                    analysis_id = result["data"]["id"]
                    await status_msg.edit(content="⏳ Récupération des résultats...")

                    # Récupère les résultats
                    async with session.get(
                        f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                        headers=headers,
                    ) as get_response:
                        if get_response.status != 200:
                            await status_msg.edit(
                                content="❌ Erreur lors de la récupération des résultats"
                            )
                            return

                        analysis_result = await get_response.json()
                        stats = analysis_result["data"]["attributes"].get("stats", {})
                        malicious = stats.get("malicious", 0)
                        suspicious = stats.get("suspicious", 0)
                        total = sum(stats.values())

                        if malicious > 0 or suspicious > 0:
                            threat_level = (
                                "🔴 Élevé"
                                if malicious > 5
                                else "🟡 Modéré" if malicious > 0 else "🟠 Faible"
                            )
                            embed = self.create_embed(
                                "⚠️ URL Potentiellement Dangereuse",
                                f"**Niveau de menace :** {threat_level}\n"
                                f"**Détections :** {malicious} malveillantes, {suspicious} suspectes\n"
                                f"**Total analyseurs :** {total}\n"
                                f"**URL analysée :** {url}",
                            )
                        else:
                            embed = self.create_embed(
                                "✅ URL Sûre",
                                f"Aucune détection sur {total} analyseurs.\n"
                                f"URL analysée : {url}",
                            )

                        await status_msg.delete()
                        await ctx.send(embed=embed)
        except Exception as e:
            await status_msg.edit(content=f"❌ Une erreur est survenue : {str(e)}")

    @app_commands.command(name="scan", description="Analyse une URL avec VirusTotal")
    @app_commands.describe(url="URL à analyser (doit commencer par http:// ou https://)")
    async def scan_slash(self, interaction: discord.Interaction, url: str):
        """Version slash command pour analyser une URL"""
        if not self.VIRUSTOTAL_API_KEY:
            await interaction.response.send_message("Erreur : la clé API VirusTotal n'est pas configurée.", ephemeral=True)
            return

        if not self.is_valid_url(url):
            await interaction.response.send_message(
                "❌ URL invalide. L'URL doit commencer par http:// ou https://", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            headers = {"x-apikey": self.VIRUSTOTAL_API_KEY}
            async with aiohttp.ClientSession() as session:
                # Soumet l'URL pour analyse
                async with session.post(
                    "https://www.virustotal.com/api/v3/urls",
                    headers=headers,
                    data={"url": url},
                ) as response:
                    if response.status != 200:
                        await interaction.followup.send("❌ Erreur lors de l'analyse", ephemeral=True)
                        return

                    result = await response.json()
                    analysis_id = result["data"]["id"]

                    # Récupère les résultats
                    async with session.get(
                        f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                        headers=headers,
                    ) as get_response:
                        if get_response.status != 200:
                            await interaction.followup.send(
                                "❌ Erreur lors de la récupération des résultats", ephemeral=True
                            )
                            return

                        analysis_result = await get_response.json()
                        stats = analysis_result["data"]["attributes"].get("stats", {})
                        malicious = stats.get("malicious", 0)
                        suspicious = stats.get("suspicious", 0)
                        total = sum(stats.values())

                        if malicious > 0 or suspicious > 0:
                            threat_level = (
                                "🔴 Élevé"
                                if malicious > 5
                                else "🟡 Modéré" if malicious > 0 else "🟠 Faible"
                            )
                            embed = self.create_embed(
                                "⚠️ URL Potentiellement Dangereuse",
                                f"**Niveau de menace :** {threat_level}\n"
                                f"**Détections :** {malicious} malveillantes, {suspicious} suspectes\n"
                                f"**Total analyseurs :** {total}\n"
                                f"**URL analysée :** {url}",
                            )
                        else:
                            embed = self.create_embed(
                                "✅ URL Sûre",
                                f"Aucune détection sur {total} analyseurs.\n"
                                f"URL analysée : {url}",
                            )

                        await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Une erreur est survenue : {str(e)}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Commandes_Webs(bot))
