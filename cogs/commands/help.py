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
                cmd_level = getattr(cmd, 'permission_level', None)
                if cmd_level is None or cmd_level in user_perms or 5 in user_perms:
                    available_commands.append(cmd)

            if not available_commands:
                continue

            embed = discord.Embed(
                title=f"📘 Aide - {cog_name}",
                description="Utilisez les flèches pour naviguer entre les pages",
                color=discord.Color.blurple()
            )

            total_commands = len([cmd for cmd in self.bot.commands])
            available_count = len(available_commands)
            
            stats = (
                "```md\n"
                "# Statistiques\n"
                f"> 📊 Commandes disponibles : {available_count}/{total_commands}\n"
                f"> 🔑 Niveau d'accès : {max(user_perms) if user_perms else 0}\n"
                "```"
            )
            
            embed.add_field(name="", value=stats, inline=False)
            embed.add_field(name="", value="━━━━━━━━━ Commandes ━━━━━━━━━", inline=False)

            for command in available_commands:
                level_txt = ""
                if hasattr(command, 'permission_level'):
                    level = getattr(command, 'permission_level')
                    if level is not None:
                        level_txt = f"[Niveau {level}] "

                help_text = command.help or 'Pas de description.'
                usage = command.usage or command.name
                
                name = f"`{usage}`"
                value = f"{level_txt}{help_text}"

                embed.add_field(name=name, value=value, inline=False)

            embed.set_footer(
                text="MathysieBot™",
                icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
            )

            embeds.append(embed)

        if not embeds:
            return await ctx.send("Aucune commande trouvée.")

        view = HelpMenu(embeds, ctx.author)
        await ctx.send(embed=embeds[0], view=view)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
print("✅ Help cog loaded")
