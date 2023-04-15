import requests
from .models import Pokemon
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView


def home(request):
    return render(request, 'home.html', )


def about(request):
    return render(request, 'about.html', )


def pokemons_view(request):
    pokemons = Pokemon.objects.all()
    return render(request, 'pokemons/pokemons_view.html', {'pokemons': pokemons, 'title': 'View Your Pokemons'})


def pokemon_detail(request, pokemon_id):
    pokemon = Pokemon.objects.get(id=pokemon_id)
    return render(request, 'pokemons/pokemon_detail.html', {'pokemon': pokemon, 'title': 'Pokemon Detail'})


class PokemonCreate(CreateView):
    model = Pokemon
    fields = '__all__'
    success_url = '/pokemons/'
    template_name = 'pokemons/pokemon_form.html'


def fetch_pokemons(request):
    pokemons = []
    for i in range(1, 5):
        url = f'https://pokeapi.co/api/v2/pokemon/{i}'
        response = requests.get(url)
        data = response.json()
        pokemon = {
            'name': data['forms'][0]['name'].capitalize(),
            'id': data['id'],
            'img': data['sprites']['other']['official-artwork']['front_default'],
        }
        pokemons.append(pokemon)
    return render(request, 'pokemons/fetch_pokemons.html', {'pokemons': pokemons, 'title': 'Fetch Pokemons'})
