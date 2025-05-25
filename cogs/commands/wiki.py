import discord
from discord.ext import commands
import requests
import logging

from utils.embed_manager import EmbedManager

logger = logging.getLogger('bot')

class WikiCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = EmbedManager.get_default_color()
        self.icon_url = "https://i.imgur.com/YSQ8PBN.png"

    def create_embed(self, title, description="", url=None, thumbnail=None):
        embed = discord.Embed(
            title=title,
            description=description,
            color=self.color,
            url=url,
            timestamp=discord.utils.utcnow()
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text="MathysieBot™ • Wikipédia", icon_url=self.icon_url)
        return embed

    async def search_wiki(self, query: str, limit: int = 5):
        """Recherche des articles Wikipedia avec extraits"""
        search_url = (
            "https://fr.wikipedia.org/w/api.php"
            "?action=query&format=json"
            "&generator=search&gsrlimit={}"
            "&prop=extracts&exintro=1&explaintext=1"
            "&gsrsearch={}".format(
                min(limit, 50),
                requests.utils.quote(query)
            )
        )
        
        try:
            response = requests.get(search_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                pages = data.get('query', {}).get('pages', {})
                results = []
                for page_id in sorted(pages.keys()):
                    page = pages[page_id]
                    results.append({
                        'title': page.get('title', ''),
                        'extract': page.get('extract', ''),
                        'pageid': page_id
                    })
                return results
            return []
        except Exception as e:
            logger.error(f"Erreur recherche Wiki: {e}")
            return []

    async def get_wiki_extract(self, title: str) -> str:
        """Récupère l'extrait d'un article Wikipedia"""
        extract_url = (
            "https://fr.wikipedia.org/w/api.php"
            "?action=query&format=json&prop=extracts"
            "&exintro=true&explaintext=true&titles={}".format(
                requests.utils.quote(title)
            )
        )
        
        try:
            response = requests.get(extract_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                pages = data.get('query', {}).get('pages', {})
                # Prendre la première page (seule page)
                page = next(iter(pages.values()))
                extract = page.get('extract', '')
                if extract:
                    # Limiter la longueur et ajouter ...
                    return extract[:500] + ('...' if len(extract) > 500 else '')
            return None
        except Exception as e:
            logger.error(f"Erreur extraction Wiki: {e}")
            return None

    def create_results_page(self, query: str, results: list, page: int, items_per_page: int = 5):
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_results = results[start_idx:end_idx]
        total_pages = (len(results) + items_per_page - 1) // items_per_page

        embed = discord.Embed(
            title="📚 Résultats de recherche Wikipédia",
            description=f"🔍 Recherche pour : **{query}**\n\n━━━━━━━━━━━━━━━━━━━━━━",
            color=self.color,
            timestamp=discord.utils.utcnow()
        )

        for i, result in enumerate(current_results, start=start_idx + 1):
            title = result['title']
            snippet = result.get('snippet', 'Pas de description disponible.')
            # Nettoie les balises HTML du snippet
            snippet = snippet.replace('<span class="searchmatch">', '**').replace('</span>', '**')
            url = f"https://fr.wikipedia.org/wiki/{requests.utils.quote(title.replace(' ', '_'))}"
            
            embed.add_field(
                name=f"{i}. {title}",
                value=f"[Voir l'article]({url})\n{snippet[:200]}...",
                inline=False
            )

        embed.set_footer(text=f"MathysieBot™ • Wikipédia | Page {page + 1}/{total_pages}", icon_url=self.icon_url)
        return embed

    async def create_single_result_embed(self, result):
        title = result['title']
        extract = result.get('extract', '')
        
        # Formater l'extrait pour un résumé plus concis
        if len(extract) > 250:  # Réduire à 250 caractères au lieu de 400
            # Trouver la dernière phrase complète
            sentences = extract[:250].split('.')
            if len(sentences) > 1:
                extract = '. '.join(sentences[:-1]) + '.'  # Prendre toutes les phrases complètes
            else:
                extract = sentences[0][:250] + "..."

        url = f"https://fr.wikipedia.org/wiki/{requests.utils.quote(title.replace(' ', '_'))}"
        
        description = (
            f"📖 **Résumé :**\n"
            f"> {extract}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📚 **[Lire l'article complet]({url})**"
        )
        
        embed = discord.Embed(
            title=f"📌 {title}",
            description=description,
            color=self.color,
            url=url
        )
        embed.set_footer(text="MathysieBot™ • Wikipédia", icon_url=self.icon_url)
        
        return embed

    class NavigationView(discord.ui.View):
        def __init__(self, cog, query: str, results: list, timeout: int = 180):
            super().__init__(timeout=timeout)
            self.cog = cog
            self.query = query
            self.results = results
            self.current_page = 0
            self.items_per_page = 5

        @discord.ui.button(label="◀️ Précédent", style=discord.ButtonStyle.primary)
        async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.current_page > 0:
                self.current_page -= 1
                embed = self.cog.create_results_page(self.query, self.results, self.current_page)
                await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="Suivant ▶️", style=discord.ButtonStyle.primary)
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if (self.current_page + 1) * self.items_per_page < len(self.results):
                self.current_page += 1
                embed = self.cog.create_results_page(self.query, self.results, self.current_page)
                await interaction.response.edit_message(embed=embed, view=self)

    @commands.command(
        name="wiki",
        help="Effectue une recherche détaillée sur Wikipédia",
        description="Recherche des articles sur Wikipédia. Affiche le résultat le plus pertinent par défaut, ou plusieurs résultats si un nombre est spécifié.",
        usage="<terme de recherche> [nombre de résultats]"
    )
    async def wiki(self, ctx, *args):
        if not args:
            embed = self.create_embed(
                "❌ Paramètre manquant", 
                "**Usage :** `!wiki <terme de recherche> [nombre de résultats]`\n\n"
                "Exemples :\n"
                "`!wiki Python` → Affiche le résultat le plus pertinent\n"
                "`!wiki Python 5` → Affiche les 5 premiers résultats",
                None
            )
            await ctx.reply(embed=embed)
            return

        # Extraire le nombre de résultats s'il est spécifié
        search_terms = list(args)
        limit = 1  # Valeur par défaut : seulement le résultat le plus pertinent
        
        # Vérifie si le dernier argument est un nombre
        if search_terms and search_terms[-1].isdigit():
            limit = min(int(search_terms.pop()), 50)  # max 50 résultats
        
        query = " ".join(search_terms)

        # Message de chargement
        loading_embed = self.create_embed("⏳ Recherche en cours", f"Recherche pour : **{query}**")
        message = await ctx.reply(embed=loading_embed)

        # Effectuer la recherche
        results = await self.search_wiki(query, limit)

        if not results:
            error_embed = self.create_embed(
                "❌ Aucun résultat",
                f"Aucun article trouvé pour : **{query}**",
                None
            )
            await message.edit(embed=error_embed)
            return

        # Utiliser un format différent pour un seul résultat
        if limit == 1:
            embed = await self.create_single_result_embed(results[0])
            await message.edit(embed=embed)
            return

        # Sinon, utiliser le format paginé normal
        embed = self.create_results_page(query, results, 0)
        view = self.NavigationView(self, query, results)
        await message.edit(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(WikiCommands(bot))
    logger.info("✅ Module Wiki chargé")