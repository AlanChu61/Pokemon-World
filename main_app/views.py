import requests
from .models import Pokemon, Player
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .forms import FeedingForm, CapturePokemonForm
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required


def home(request):
    return render(request, 'home.html', {'title': 'HomePage'})


def about(request):
    return render(request, 'about.html', {'title': 'AboutPage'})


@login_required
def pokemons_view(request):
    pokemons = Pokemon.objects.filter(ownedby=request.user)
    return render(request, 'pokemons/pokemons_view.html', {'pokemons': pokemons, 'title': 'View Your Pokemons'})


def pokemon_detail(request, pokemon_id):
    feeding_form = FeedingForm()
    pokemon = Pokemon.objects.get(id=pokemon_id)
    print(pokemon.evolve_chains)
    check_items_evolve(request, pokemon_id)
    return render(request, 'pokemons/pokemon_detail.html', {'pokemon': pokemon, 'title': 'Pokemon Detail', 'user': request.user, 'feeding_form': feeding_form})


def level_up(request, pokemon_id):
    pokemon = Pokemon.objects.get(id=pokemon_id)
    if request.method == 'POST':
        pokemon.level_up()
        return redirect('pokemon_detail', pokemon_id=pokemon.id)


def pokemon_pocket_box(request, pokemon_id):
    pokemon = Pokemon.objects.get(id=pokemon_id)
    print(pokemon.name)
    print(pokemon.in_pocket)
    if request.method == 'POST':
        if pokemon.in_pocket:
            pokemon.in_pocket = False
        else:
            pokemon.in_pocket = True
        pokemon.save()
        return redirect('pokemons_view')


def check_evolve(pokemon_id):
    url = f'https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}'
    response = requests.get(url)
    data = response.json().get('evolution_chain').get('url')
    data = requests.get(data).json()
    item = None
    min_level = data['chain']['evolves_to'][0]['evolution_details'][0]['min_level']
    if min_level != None:
        evole_to = data['chain']['evolves_to'][0]['species']['name']
    else:
        evole_to = data['chain']['evolves_to'][0]['evolves_to'][0]['species']['name']
        item = data['chain']['evolves_to'][0]['evolves_to'][0]['evolution_details'][0]['item']['name']

    print(min_level, evole_to, item)
    return {'evole_to': evole_to, 'min_level': min_level, 'item': item}


def check_items_evolve(request, pokemon_id):
    # check pokemon
    pokemon = Pokemon.objects.get(id=pokemon_id)
    player = Player.objects.get(ownedby=request.user)
    items = player.items.keys()
    required_evolve_item = pokemon.evolve_chains['item']
    if required_evolve_item in list(items):
        pokemon.ready_to_evolve = True
        pokemon.save()
        print(
            f"{pokemon} is ready to evolve to {pokemon.evolve_chains['evole_to']}")
        return True
    else:
        return False


def evolve_pokemon(request, pokemon_id):
    pokemon = Pokemon.objects.get(id=pokemon_id)
    if request.method == 'POST':
        if pokemon.ready_to_evolve:
            pokemon.evolve(pokemon.evolve_chains['evole_to'])
            return redirect('pokemon_detail', pokemon_id=pokemon.id)
        else:
            return redirect('pokemon_detail', pokemon_id=pokemon.id)


def capture_pokemon(request, pokemon_id):
    capture_pokemon_id = request.POST.get('pokemon_id')
    captured_pokemon = fetch_pokemon(capture_pokemon_id)
    name = captured_pokemon['name']
    level = 5
    img = captured_pokemon['img']
    evolve_chains = check_evolve(capture_pokemon_id)
    ownedby = request.user
    in_pocket = True if len(
        Pokemon.objects.filter(in_pocket=True)) < 6 else False
    new_pokemon = CapturePokemonForm(
        {'pokemon_id': capture_pokemon_id, 'name': name, 'level': level, 'img': img, 'ownedby': ownedby,  'in_pocket': in_pocket, "evolve_chains": evolve_chains})
    new_pokemon.save()
    return redirect('fetch_pokemons')


class PokemonCreate(CreateView):
    model = Pokemon
    fields = '__all__'
    success_url = '/pokemons/'
    template_name = 'pokemons/pokemon_form.html'


class PokemonRelease(DeleteView):
    model = Pokemon
    success_url = '/pokemons/'
    template_name = 'pokemons/pokemon_confirm_delete.html'


def fetch_pokemon(id):
    url = f'https://pokeapi.co/api/v2/pokemon/{id}'
    response = requests.get(url)
    data = response.json()
    pokemon = {
        'name': data['forms'][0]['name'].capitalize(),
        'id': data['id'],
        'img': data['sprites']['other']['official-artwork']['front_default'],
        # 'moves': data['moves'][0],
    }
    return pokemon


def fetch_pokemons(request):
    pokemons = []
    for i in range(1, 26):
        pokemon = fetch_pokemon(i)
        pokemons.append(pokemon)
    return render(request, 'pokemons/fetch_pokemons.html', {'pokemons': pokemons, 'title': 'Fetch Pokemons'})


def add_feeding(request, pokemon_id):
    form = FeedingForm(request.POST)
    if form.is_valid():
        new_feeding = form.save(commit=False)
        new_feeding.pokemon_id = pokemon_id
        new_feeding.save()
        Pokemon.objects.get(id=pokemon_id).is_level_up()
    return redirect('pokemon_detail', pokemon_id=pokemon_id)


def signup(request):
    error_message = ''
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            error_message = 'Invalid sign up - try again'
    form = UserCreationForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)


def store(request):
    url = 'https://pokeapi.co/api/v2/item-category/10/'
    response = requests.get(url)
    data = response.json()
    items = []
    for item in data['items']:
        item_name = item['name']
        item_url = item['url']
        item = fetch_item(item_name, item_url)
        if item != None:
            items.append(item)
    return render(request, 'store/store_view.html', {'title': 'Store', 'items': items})


def fetch_item(name, url):
    # https://pokeapi.co/api/v2/item/80/
    response = requests.get(url)
    data = response.json()
    if data['cost'] and data['sprites']['default']:
        print(name)
        item = {
            'name': name,
            'cost': data['cost'],
            'img': data['sprites']['default'],
        }
        return item


class PlayerCreate(CreateView):
    model = Player
    fields = ("name", "money")
    success_url = "player/player_profile.html"
    template_name = "player/player_form.html"

    def form_valid(self, form):
        form.instance.ownedby = self.request.user
        return super().form_valid(form)


def player_profile(request):
    player = Player.objects.get(ownedby=request.user)
    pokemons = Pokemon.objects.filter(ownedby=request.user)
    pokemons_count = pokemons.count()
    items = {}
    for item, qty in player.items.items():
        items[item] = qty
    print(items)
    pokemons_in_pocket = Pokemon.objects.filter(
        ownedby=request.user, in_pocket=True)
    return render(request, 'player/player_profile.html', {'player': player,  'pokemons': pokemons, 'pokemon_count': pokemons_count,
                                                          'pokemons_in_pocket': pokemons_in_pocket, 'title': 'Player Profile', 'items': items})
