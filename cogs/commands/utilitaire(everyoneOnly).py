import discord
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

    def create_embed(self, title, description=None, color=None):
        """Crée un embed standard"""
        if color is None:
            color = EmbedManager.get_default_color()
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Bot Discord - Utilitaires Web")
        return embed

    def is_valid_url(self, url):
        """Vérifie si l'URL est valide (http:// ou https://)."""
        try:
            result = urlparse(url)
            return result.scheme in ['http', 'https'] and result.netloc
        except ValueError:
            return False

    @commands.command(
        name="shorten",
        help="Raccourcit une URL",
        description="Utilise l'API Bitly pour raccourcir une URL longue",
        usage="<url>"
    )
    async def shorten_url(self, ctx, url: str):
        if not self.BITLY_API_KEY:
            await ctx.send("Erreur : la clé API Bitly n'est pas configurée.")
            return

        if not self.is_valid_url(url):
            await ctx.send("❌ URL invalide. L'URL doit commencer par http:// ou https://")
            return

        try:
            headers = {
                'Authorization': f'Bearer {self.BITLY_API_KEY}',
                'Content-Type': 'application/json'
            }
            response = requests.post('https://api-ssl.bitly.com/v4/shorten', 
                                   headers=headers, 
                                   json={'long_url': url})
            
            if response.status_code == 200:
                short_url = response.json().get('link')
                embed = self.create_embed("🔗 URL Raccourcie", f"URL d'origine : {url}\nURL courte : {short_url}")
                await ctx.send(embed=embed)
            else:
                error_msg = response.json().get("message", "Erreur inconnue")
                await ctx.send(f'❌ Erreur lors du raccourcissement de l’URL : {error_msg}')
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

    @commands.command(
        name="qrcode",
        help="Génère un QR Code",
        description="Crée un QR Code à partir d'une URL",
        usage="<url>"
    )
    async def generate_qrcode(self, ctx, url: str):
        if not self.is_valid_url(url):
            await ctx.send("❌ URL invalide. L'URL doit commencer par http:// ou https://")
            return
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            embed = self.create_embed("📱 QR Code généré", f"URL encodée : {url}")
            await ctx.send(embed=embed, file=discord.File(buffer, filename="qrcode.png"))
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

    @commands.command(
        name="scan",
        help="Analyse une URL",
        description="Vérifie si une URL est potentiellement malveillante via VirusTotal",
        usage="<url>"
    )
    async def scan_url(self, ctx, url: str):
        if not self.VIRUSTOTAL_API_KEY:
            await ctx.send("Erreur : la clé API VirusTotal n'est pas configurée.")
            return

        if not self.is_valid_url(url):
            await ctx.send("❌ URL invalide. L'URL doit commencer par http:// ou https://")
            return

        status_msg = await ctx.send("🔎 Analyse en cours...")
        try:
            headers = {'x-apikey': self.VIRUSTOTAL_API_KEY}
            async with aiohttp.ClientSession() as session:
                # Soumet l'URL pour analyse
                async with session.post('https://www.virustotal.com/api/v3/urls', 
                                     headers=headers, 
                                     data={'url': url}) as response:
                    if response.status != 200:
                        await status_msg.edit(content="❌ Erreur lors de l'analyse")
                        return
                    
                    result = await response.json()
                    analysis_id = result['data']['id']
                    await status_msg.edit(content="⏳ Récupération des résultats...")

                    # Récupère les résultats
                    async with session.get(f'https://www.virustotal.com/api/v3/analyses/{analysis_id}', 
                                         headers=headers) as get_response:
                        if get_response.status != 200:
                            await status_msg.edit(content="❌ Erreur lors de la récupération des résultats")
                            return
                        
                        analysis_result = await get_response.json()
                        stats = analysis_result['data']['attributes'].get('stats', {})
                        malicious = stats.get('malicious', 0)
                        suspicious = stats.get('suspicious', 0)
                        total = sum(stats.values())

                        if malicious > 0 or suspicious > 0:
                            threat_level = "🔴 Élevé" if malicious > 5 else "🟡 Modéré" if malicious > 0 else "🟠 Faible"
                            embed = self.create_embed(
                                "⚠️ URL Potentiellement Dangereuse",
                                f"**Niveau de menace :** {threat_level}\n"
                                f"**Détections :** {malicious} malveillantes, {suspicious} suspectes\n"
                                f"**Total analyseurs :** {total}\n"
                                f"**URL analysée :** {url}"
                            )
                        else:
                            embed = self.create_embed(
                                "✅ URL Sûre",
                                f"Aucune détection sur {total} analyseurs.\n"
                                f"URL analysée : {url}"
                            )
                        
                        await status_msg.delete()
                        await ctx.send(embed=embed)
        except Exception as e:
            await status_msg.edit(content=f"❌ Une erreur est survenue : {str(e)}")

async def setup(bot):
    await bot.add_cog(Commandes_Webs(bot))
