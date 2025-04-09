import random
from django.shortcuts import render
from .context_items import ContextItems

def get_random_context():
    context = {
        "header": random.choice(ContextItems.headers),
        "home_layout": random.choice(ContextItems.home_layouts),
        "footer": random.choice(ContextItems.footers),
        "bg_gradient": random.choice(ContextItems.bg_gradients),
    }
    
    return context