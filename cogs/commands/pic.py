import discord
from discord.ext import commands

class ProfilePictureCog(commands.Cog):
    """Commandes pour afficher les photos de profil des utilisateurs"""
    
    def __init__(self, bot):
        self.bot = bot
        print("Cog ProfilePicture chargé et prêt à utiliser la commande +pic")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog ProfilePicture connecté en tant que {self.bot.user}')
    
    @commands.command()
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
        embed = discord.Embed(
            title=f"Photo de profil de {member.display_name}", 
            color=discord.Color.blue()
        )
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"ID: {member.id}")
        
        # Envoyer l'embed avec l'avatar
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ProfilePictureCog(bot))