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

    @commands.command(name='help')
    async def help_command(self, ctx):
        user_perms = self.bot.perm_manager.get_user_permissions(ctx.author.id)
        embeds = []

        for cog_name, cog in self.bot.cogs.items():
            available_commands = []
            for cmd in cog.get_commands():
                # Si la commande n'a pas de niveau défini, elle est accessible à tous
                cmd_level = getattr(cmd, 'permission_level', None)
                
                # Ajouter la commande si:
                # 1. Pas de niveau requis (None)
                # 2. Utilisateur a le niveau requis
                # 3. Utilisateur est niveau 5 (admin système)
                if cmd_level is None or cmd_level in user_perms or 5 in user_perms:
                    available_commands.append(cmd)

            if not available_commands:
                continue

            embed = discord.Embed(
                title=f"📘 Aide - {cog_name}",
                color=discord.Color.blurple()
            )

            for command in available_commands:
                # Afficher le niveau uniquement si la commande en a un
                level_txt = ""
                if hasattr(command, 'permission_level'):
                    level = getattr(command, 'permission_level')
                    if level is not None:
                        level_txt = f"[Niveau {level}] "

                embed.add_field(
                    name=f"{command.name}",
                    value=f"{level_txt}\n**Usage :** `{ctx.prefix}{command.name} {command.usage or ''}`\n{command.help or 'Pas de description.'}`",
                    inline=False
                )

            # Ajouter des stats en bas de l'embed
            total_commands = len([cmd for cmd in self.bot.commands])
            available_count = len(available_commands)
            
            embed.set_footer(text=(
                f"📊 {available_count}/{total_commands} commandes disponibles • "
                f"Niveau d'accès: {max(user_perms) if user_perms else 0}"
            ))

            embeds.append(embed)

        if not embeds:
            return await ctx.send("Aucune commande trouvée.")

        view = HelpMenu(embeds, ctx.author)
        await ctx.send(embed=embeds[0], view=view)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
print("✅ Help cog loaded")
