import discord
from discord.ext import commands

class HelpMenu(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author: discord.User):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.author = author
        self.index = 0

    async def update(self, interaction: discord.Interaction):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = False

        # Désactive les boutons si aux extrêmes
        if self.index == 0:
            self.previous_button.disabled = True
        if self.index == len(self.embeds) - 1:
            self.next_button.disabled = True

        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(label='⬅️', style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("Tu ne peux pas utiliser ces boutons.", ephemeral=True)

        self.index -= 1
        await self.update(interaction)

    @discord.ui.button(label='➡️', style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("Tu ne peux pas utiliser ces boutons.", ephemeral=True)

        self.index += 1
        await self.update(interaction)

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help', help="Affiche l'aide du bot.")
    async def help_command(self, ctx):
        # Récupérer les cogs
        embeds = []
        for cog_name, cog in self.bot.cogs.items():
            if not cog.get_commands():
                continue
            embed = discord.Embed(title=f"📘 Aide - {cog_name}", color=discord.Color.blurple())
            for command in cog.get_commands():
                embed.add_field(
                    name=command.name,
                    value=f"**Usage :** `{ctx.prefix}{command.name} {command.usage or ''}`\n{command.help or 'Pas de description.'}",
                    inline=False
                )
            embeds.append(embed)

        if not embeds:
            return await ctx.send("Aucune commande trouvée.")

        view = HelpMenu(embeds, ctx.author)
        await ctx.send(embed=embeds[0], view=view)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
print("✅ Help cog loaded")