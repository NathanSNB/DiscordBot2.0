from discord.ext import commands

def require_permission(level: int):
    async def predicate(ctx):
        return ctx.bot.perm_manager.has_permission(ctx.author.id, level)
    return commands.check(predicate)

def require_permissions(levels: list):
    async def predicate(ctx):
        user_perms = ctx.bot.perm_manager.get_user_permissions(ctx.author.id)
        return all(level in user_perms for level in levels)
    return commands.check(predicate)