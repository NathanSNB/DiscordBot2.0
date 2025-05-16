import discord

class EmbedManager:
    @staticmethod
    def create_embed(title, description=None, color=discord.Color(0x2BA3B3), fields=None, thumbnail=None, image=None):
        """Crée un embed standard pour tous les cogs"""
        embed = discord.Embed(
            title=title, 
            description=description,
            color=color
        )
        
        if fields:
            for field in fields:
                embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field.get('inline', False)
                )
                
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        if image:
            embed.set_image(url=image)
            
        return embed

    @staticmethod
    def create_welcome_dm(member: discord.Member, rules_channel: discord.TextChannel) -> discord.Embed:
        """Crée un embed d'accueil pour les messages privés"""
        embed = discord.Embed(
            title=f"🌟 Bienvenue sur {member.guild.name} !",
            description=(
                "Nous sommes enchantés de t'accueillir parmi nous !\n"
                "Pour que ton intégration se passe au mieux, voici quelques étapes à suivre :"
            ),
            color=discord.Color(0x2BA3B3)
        )

        # Étapes à suivre
        embed.add_field(
            name="📝 Première étape",
            value=f"Rends-toi dans le salon {rules_channel.mention}",
            inline=False
        )

        embed.add_field(
            name="📖 Deuxième étape",
            value="Lis attentivement le règlement qui s'y trouve",
            inline=False
        )

        embed.add_field(
            name="✅ Dernière étape",
            value="Clique sur la réaction ✅ sous le règlement pour obtenir accès au serveur",
            inline=False
        )

        # Ajout d'un footer informatif
        embed.set_footer(
            text="Une fois ces étapes terminées, tu auras accès à l'ensemble du serveur !"
        )

        # Ajout de l'icône du serveur si disponible
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)

        return embed

    @staticmethod
    def create_access_granted(guild: discord.Guild, roles_channel: discord.TextChannel) -> discord.Embed:
        """Crée un embed de confirmation d'accès avec les informations sur les rôles"""
        embed = discord.Embed(
            title="✅ Accès accordé !",
            description=(
                f"Bienvenue officiellement sur **{guild.name}** !\n"
                f"Tu as maintenant accès à l'ensemble du serveur."
            ),
            color=discord.Color.green()
        )

        # Ajout des informations sur les rôles
        embed.add_field(
            name="🎭 Attribution des Rôles",
            value=f"Rends-toi dans {roles_channel.mention} pour choisir tes rôles !",
            inline=False
        )

        embed.add_field(
            name="📋 Comment faire ?",
            value="Choisis les rôles qui t'intéressent en cliquant sur les réactions correspondantes.",
            inline=False
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        return embed

    @staticmethod
    def create_access_granted_dm(guild=None, roles_channel=None) -> discord.Embed:
        """Crée un embed pour le message de bienvenue en DM"""
        embed = discord.Embed(
            title="✅ Accès accordé !",
            description=f"Bienvenue officiellement sur {guild.name if guild else 'notre serveur'} !\nTu as maintenant accès à l'ensemble du serveur.",
            color=discord.Color.green()
        )

        if roles_channel:
            embed.add_field(
                name="🎭 Attribution des Rôles",
                value=f"Rends-toi dans {roles_channel.mention} pour choisir tes rôles !",
                inline=False
            )

        if guild and guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        return embed

