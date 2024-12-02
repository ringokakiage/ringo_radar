# Ringo Radar - Scouting app for South American players - code by ringokakiage #
import streamlit as st
import numpy as np
import pandas as pd
from mplsoccer import PyPizza, FontManager, Sbopen
from scipy import stats

# Load the soccer data
parser = Sbopen()

# Load the fonts for the pizza plot
font_normal = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/'
                          'src/hinted/Roboto-Regular.ttf')
font_italic = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/'
                          'src/hinted/Roboto-Italic.ttf')
font_bold = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/'
                        'RobotoSlab[wght].ttf')

# Title and subtitle
st.title("Ringo Radar")
st.subheader("Criado por ringokakiage | Database: Wyscout")
st.write("Com este aplicativo, você pode gerar o radar de impacto, ou Ringo Radar, de jogadores sul-americanos em ligas de interesse para o scouting do seu time.\n Você pode utilizar as imagens geradas pela ferramenta, desde que os créditos ao autor sejam devidamente atribuídos. | Inspiração: @BenGriffis")

# Load the database
wyscout = pd.read_csv("wyscout_database_nov2024.csv")

# Version 1.01 - fixed a bug where some players radar were not being generated correctly.

# Sidebar with filters
with st.sidebar:
    st.header("Selecione os filtros")

    # Step 1: Select the league
    league = st.selectbox("Selecione a liga", wyscout["League"].sort_values().unique())

    # Step 2: Select the team based on the league
    teams = wyscout[wyscout["League"] == league]["Team within selected timeframe"].sort_values().unique()
    team = st.selectbox("Selecione o time", teams)

    # Step 3: Select the player based on the team
    players = wyscout[wyscout["Team within selected timeframe"] == team]["Player"].sort_values().unique()
    player = st.selectbox("Selecione o jogador", players)

    pos_options = wyscout[
    (wyscout["Player"] == player) & 
    (wyscout["Team within selected timeframe"] == team)]["Position"]

    if pos_options.empty:
        st.error(f"No position data found for player: {player} in team: {team}.")
        position_list = []
    else:
        # Get the first row for the matching player-team combination
        pos_options = pos_options.iloc[0]
        position_list = sorted([pos.strip() for pos in pos_options.split(",")])

    position = st.selectbox("Selecione a posição", position_list)

    # Step 5: Slider for minimum minutes
    min_minutes = st.slider(
        "Selecione o mínimo de minutos jogados", 
        min_value=300, 
        max_value=800, 
        value=500
    )

    # Value display
    value_display = st.selectbox("Valores do radar:", ["Percentile", "Index values"])

    comparison_scope = st.selectbox(
        "Compare o jogador com:",
        ["Toda a base de dados", "Jogadores da mesma liga"]
    )
    st.write("Database atualizada até Novembro de 2024")

# Normalize positions in the dataframe
def normalize_positions(df, position_map):
    position_cols = ["Primary position", "Secondary position", "Third position"]
    for col in position_cols:
        df[col] = df[col].apply(lambda x: position_map.get(x, x) if pd.notna(x) else "Unknown")
    return df

# Define the position map
position_map = {
    "GK": "GK",
    "CB": "CB",
    "RCB": "CB",
    "LCB": "CB",
    "RCB3": "CB",
    "LCB3": "CB",
    "LB": "LB",
    "LWB": "LB",
    "RB": "RB",
    "RWB": "RB",
    "RB5": "RB",
    "LB5": "LB",
    "DMF": "DMF",
    "LDMF": "DMF",
    "RDMF": "DMF",
    "CMF": "CMF",
    "LCMF": "CMF",
    "RCMF": "CMF",
    "CMF3": "CMF",
    "LCMF3": "CMF",
    "RCMF3": "CMF",
    "AMF": "AMF",
    "LAMF": "AMF",
    "RAMF": "AMF",
    "CF": "CF",
    "LW": "WIN",
    "RW": "WIN",
    "LWF": "WIN",
    "RWF": "WIN"
}

# Normalize positions in the original dataframe
wyscout = normalize_positions(wyscout, position_map)

# Create dataframes for each position
def create_position_dfs(position_key, df, graph_minutes=min_minutes):
    temp_df = df[
        (df["Minutes played"] >= graph_minutes) & 
        (df[["Primary position", "Secondary position", "Third position"]].apply(lambda x: position_key in x.values, axis=1))
    ]
    result_df = temp_df.drop_duplicates(subset=["Wyscout id", "Team within selected timeframe", "League", "Position"], keep="first")
    return result_df

position_dfs = {}
for key in position_map.values():
    position_dfs[key] = create_position_dfs(key, wyscout)

# Filter data based on the selected player, team, league, and position
def filter_data(wyscout, league, team, player, position):
    filtered_data = wyscout[
        (wyscout["League"] == league) & 
        (wyscout["Team within selected timeframe"] == team) & 
        (wyscout["Player"] == player) & 
        (wyscout[["Primary position", "Secondary position", "Third position"]].apply(lambda x: position in x.values, axis=1))
    ]
    return filtered_data

chosen_player_minutes = wyscout[(wyscout["Player"] == player) & 
                                (wyscout["Team within selected timeframe"] == team) & 
                                (wyscout["League"] == league)]["Minutes played"].iloc[0]
if chosen_player_minutes < min_minutes:
    st.warning(f"O jogador {player} não jogou minutos suficientes ({chosen_player_minutes}).")

player_data = filter_data(wyscout, league, team, player, position)

positions_gk = ['GK']

# Defenders
positions_cb = ['CB', 'RCB', 'LCB', 'RCB3', 'LCB3']
positions_lb = ['LB','LWB', 'LB5',]
positions_rb = ['RB','RWB', 'RB5',]


# Midfielders
positions_dmf = ['DMF', 'LDMF', 'RDMF',]
positions_cmf = ['RCMF', 'LCMF', 'LCMF3', 'RCMF3', 'CMF',]
positions_amf = ['AMF', 'LAMF', 'RAMF']

# Forwards
positions_cf = ['CF']
positions_win = ['LW', 'RW', 'LWF', 'RWF']

# Filter players based on the selected position
if comparison_scope == "Toda a base de dados":
    # Use the full dataframe for the selected position
    selected_key = position_map.get(position, position)  # Get the canonical position key
    player_df_filtered = position_dfs.get(selected_key, pd.DataFrame()).copy()
else:
    # Filter the position dataframe by the selected league
    selected_key = position_map.get(position, position)
    player_df_filtered = position_dfs.get(selected_key, pd.DataFrame())
    player_df_filtered = player_df_filtered[player_df_filtered["League"] == league].copy()


# Define the pizza variables
pizza_var_names_dict = {
    # general stats, simple, 16 (4 of each category)
    'metrics': [
        'wSwC', 'wAwC', 'wDcwC', 'Aerial impact', 'wDpwC','wPwC'
    ],

    'swc': ['Goal conversion, %', 'Shots on target per 90', 'Shots on target, %', 'SoT pTt',
                    'Touches in box per 90', 'SoT/RB', 'Goal pTt',
           ],
    
    
    'gen': [
        'Non-penalty goals per 90', 'npxG per 90', 'npxG per shot',
        'Shots per 90', 'Goal conversion, %',
        
        'xA per 90', '1st, 2nd, 3rd assists', 'Shot assists per 90', 
        'Crosses per 90', 'Accurate crosses, %', 
        'Accurate passes, %','Accurate long passes, %',
        
        'Successful dribbles per 90', 'Offensive duels won, %', 
        'Progressive passes per 90', 'Progressive runs per 90', 

        'Aerial duels per 90','Aerial duels won, %', 
        'Shots blocked per 90', 'Defensive duels won, %', 'PAdj Interceptions', 'PAdj Sliding tackles'
    ],

    'att': [
        'Non-penalty goals per 90', 'npxG per 90', 'Shots per 90', 'Shots on target per 90', 
        'Goal conversion, %', 'npxG per shot',
        # 'xA per 90', 'xA per 90 Ctb %','1st, 2nd, 3rd assists', 'Shot assists per 90',
        'Offensive duels won per 90', 'Offensive duels won, %', 'Offensive duels per 90 Ctb %',
        'Accelerations per 90', 'Progressive runs per 90', 'Touches in box per 90', 'Touches in box per 90 Ctb %',
        'Dribbles per 90', 'Successful dribbles, %', 'Dribbles per 90 Ctb %',
        'Fouls suffered per 90',
    ],
    'pass': [
        'xA per 90','1st, 2nd, 3rd assists', 'Shot assists per 90',
        'Crosses per 90','Accurate crosses, %', 'Crosses per 90 Ctb %',
        'PwC',
        'Long passes per 90', 'Accurate long passes, %', 
        'Passes per 90', 'Accurate passes per 90', 
        'Progressive passes per 90', 'Accurate progressive passes, %',  
        'Forward passes per 90', 'Accurate forward passes, %','Passes to final third per 90', 'Accurate passes to final third, %', 
        # 'Accelerations per 90', 'Progressive runs per 90', 'Touches in box per 90', 'Touches in box per 90 Ctb %',
    ],
    'def': [
        'Defensive duels won per 90', 'Defensive duels won, %', 'Aerial duels won, %', 'PAdj Interceptions',
        'PAdj Sliding tackles', 'Shots blocked per 90', 'Fouls per 90', 'Cards per 90'
    ]
}

# Define the pizza variables with spaces (necessary for the pizza plot)
pizza_var_names_spaced_dict = {
    'metrics': [
        'Shooting', 'Attacking', 'Positional\ndefense','Aerial impact', 'Reactive\ndefense', 'Passing',
    ],

     'swc': ['Goal conversion, %', 'Shots on target\n per 90', 'Shots\n on target, %', 'SoT pTt',
                    'Touches in box\n per 90', 'SoT/RB', 'Goal pTt',
           ],
    
    
     'gen': [
        'npGoals\n(90)', 'npxG\n(90)', 'npxG/shot',
        'Shots\n(90)', 'Goal/SoT\n success (%)',
        
        'xA\n(90)', '1st, 2nd, 3rd\n assist (90)', 'Shot\nassist (90)', 
        'Crosses\n(90)', 'Cross\nacc. (%)', 
        'Pass\nacc. (%)', 'Long pass\nacc. (%)', 
        
        'Success\ndribble (90)', 'Off. duel\nwon (%)', 
        'Prog.\npasses (90)', 'Prog.\nruns (90)', 

        'Aerial\nduels (90)', 'Aerial\nwins (%)',
        'Shot\nblocks (90)', 'Def. duels\nwon (%)', 'PAdj\nInt (90)', 'PAdj\ntackles (90)'
    ],

    # 'gen': [
    #     'npG\n (90)', 'npxG\n(90)',
    #     'Shots (90)', 'AwC',
    #     '1st, 2nd, 3rd\n assists (90)', 'xA (90)', 'PwC', 'Crosses\n (90)', 
    #     'Offensive duels\n won (%)', 'Successful\n dribbles (90)', 
    #     'Prog.\n passes (90)', 'Prog.\n runs (90)', 'DwC',
    #     'Aerial\n duels won (%)','Shots', 'Def. duels\n won (%)', 'PAdj\n Interceptions (90)', 'PAdj\n Tackles (90)'
    
    # ],
    'att': [
        'npG\n (90)', 'npxG\n (90)', 'Shots (90)', 'SoT (90)', 
        'G/s\n conversion, %', 'npxG/\nshot',
        # 'xA per 90','xA per 90\n Ctb %','1st, 2nd, 3rd\n assists', 'Shot assists\n per 90',
        'Off. duels\n won (90)','Off. duels\n won (%)', 'Off. duels\n player/team (%)',
        'Accelerations','Prog.\n runs (90)','Touches in\n box per 90','Touches in\n box per 90 Ctb %',
        'Dribbles\n (90)','Successful\n dribbles (%)','Dribbles\n per 90 Ctb %','Fouls\n suffered (90)',
    ],
    

    'pass': [
        'xA\n(90)','1st, 2nd, 3rd\n assists (90)', 'Shot\n assists (90)',
        'Crosses per 90', 'Accurate\n crosses, %', 'Crosses\n (indCtb %',
        'PwC',
        'Long\n passes per 90', 'Accurate\n long passes, %', 
        'Passes per 90', 'Accurate\n passes, %', 
        'Progressive\n passes per 90', 'Accurate\n progressive passes, %', 
        'Forward\n passes per 90', 'Accurate\n forward passes, %','Passes to\n final third per 90', 'Accurate passes\n to final third, %', 
        # 'Accelerations per 90', 'Progressive runs per 90', 'Touches in box per 90', 'Touches in box per 90 Ctb %',
    ],
    
    'def': [
        'Defensive duels\n won per 90', 'Defensive duels\n won, %', 'Aerial duels won, %',
        'PAdj\n Interceptions','PAdj\n Sliding tackles', 'Shots blocked\n per 90',
        'Fouls per 90','Cards per 90',
    ]
}


def map_primary_position(player_position):
    # Split positions if multiple exist
    positions = player_position.split(", ")
    
    # Map each position to its category
    mapped_positions = [position_map.get(pos.strip(), None) for pos in positions]
    
    # Filter out unmapped positions
    valid_positions = [pos for pos in mapped_positions if pos]
    
    # Return the primary (first) valid position or None
    return valid_positions[0] if valid_positions else None


def create_pizza_plot(player_info, position_dfs, plot_type):
    # Unpack player info
    player_league, player_team, player_name, player_position = player_info
# Map primary position
    primary_position = map_primary_position(player_position)
    if not primary_position:
        st.error(f"Positions {player_position} are not categorized.")
        return None
    
    # Determine which dataframe to use
    position_key = ''
    if primary_position in positions_gk:
        position_key = 'GK'
    elif primary_position in positions_cb + positions_lb + positions_rb:
        position_key = 'CB' if primary_position in positions_cb else 'LB' if primary_position in positions_lb else 'RB'
    elif primary_position in positions_dmf + positions_cmf + positions_amf:
        position_key = 'DMF' if primary_position in positions_dmf else 'CMF' if primary_position in positions_cmf else 'AMF'
    elif primary_position in positions_win:
        position_key = 'WIN'
    elif primary_position in positions_cf:
        position_key = 'CF'
    
    # Check if position_key was determined
    if not position_key:
        st.error(f"Primary position {primary_position} not categorized.")
        return None
    
    # Select the correct dataframe
    player_df = position_dfs.get(position_key)
    if player_df is None:
        st.error(f"No data available for position: {primary_position}")
        return None
    
    # Filter the player's data
    jogador_pizza = player_df.loc[
        (player_df['League'] == player_league) &
        (player_df['Player'] == player_name) &
        (player_df['Team within selected timeframe'] == player_team) 
    ]
    
    if jogador_pizza.empty:
        st.error(f"No data found for player: {player_name} in team: {player_team} under position: {primary_position}")
        # return None
        
    # Number of players in the database
    num_players = player_df.shape[0]

    # Select the columns to be used in the pizza plot
    jogador_pizza_1 = jogador_pizza.select_dtypes(exclude='object').copy()
    pizza_var_names = pizza_var_names_dict[plot_type]
    pizza_var_names_spaced = pizza_var_names_spaced_dict[plot_type]
    jogador_pizza_1_1 = jogador_pizza_1[pizza_var_names]
    jogador_colunas = jogador_pizza_1_1.columns[0:]

    # Extract values and calculate percentiles
    valores_colunas = [jogador_pizza_1_1[column].iloc[0] for column in jogador_colunas]
    percent_jogador = []
    for column in jogador_colunas:
        if column in ['Fouls per 90', 'Cards per 90']:
            percentile = 100 - stats.percentileofscore(player_df_filtered[column], jogador_pizza_1_1[column].iloc[0])
        else:
            percentile = stats.percentileofscore(player_df_filtered[column], jogador_pizza_1_1[column].iloc[0])
            percent_jogador.append(percentile)
    percent_jogador = np.around(percent_jogador, 2)

    # Determine slice colors based on percentage values
    slice_colors = [
        '#a20e0e' if value <= 30 else '#d8580b' if 30 < value <= 45 else '#f6d354' if 45 < value <= 65 else '#329999' if 65<value<=80 else '#396892' if 80 < value <= 95 else '#814a66'
        for value in percent_jogador
    ]

    # Determine text colors based on slice colors
    text_colors = [
        'black' if color == '#f6d354' else 'white'
        for color in slice_colors
    ]

    # Create the pizza plot
    baker = PyPizza(
        params=pizza_var_names_spaced,
        min_range=None,
        max_range=None,
        straight_line_color="#F2F2F2",
        straight_line_lw=1,
        last_circle_lw=0,
        other_circle_lw=1,
        other_circle_ls="-.",
        inner_circle_size=20,  # size of inner circle
    )
    
    # Make the pizza plot
    fig, ax = baker.make_pizza(
        percent_jogador,
        figsize=(12, 12),
        param_location=110,
        slice_colors=slice_colors,
        value_colors=text_colors,
        value_bck_colors=slice_colors,
        color_blank_space="same",
        blank_alpha=0.25,
        kwargs_slices=dict(
            facecolor="cornflowerblue", edgecolor="#F2F2F2",
            zorder=2, linewidth=1
        ),
        kwargs_params=dict(
            color="#000000", fontsize=12,
            fontproperties=font_normal.prop, va="center"
        ),
        kwargs_values=dict(
            color="#000000", fontsize=12,
            fontproperties=font_normal.prop, zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="cornflowerblue", lw=1
            )
        )
    )

    # Put the values in the pizza plot
    texts = baker.get_value_texts()
    for i, text in enumerate(texts):
        if value_display == "Percentile":
            text.set_text(f"{percent_jogador[i]:.2f}")
        elif value_display == "Index values":
            text.set_text(f"{valores_colunas[i]:.2f}")


    # Get the player info
    player_league = jogador_pizza.iloc[0]['League']
    player_age = jogador_pizza.iloc[0]['Age']
    player_position = jogador_pizza.iloc[0]['Primary position']
    player_club = jogador_pizza.iloc[0]['Team within selected timeframe']
    player_league = jogador_pizza.iloc[0]['League']
    player_minutes = jogador_pizza.iloc[0]['Minutes played']
    
    # Create the title and subtitle
    file_suffix = {'att': 'attacking', 'pass': 'passing', 'def': 'defensive', 'gen': 'general', 'metrics': 'user metrics', 'swc': 'swc metrics'}[plot_type]

    title = f'{player_name}, Age: {player_age}, {player_position}, {player_minutes} minutes, {player_club}'
    subtitle = f'League: {player_league}, Percentile rankings: {file_suffix}'

    # Add title
    fig.text(
        0.515, 0.97, title, size=16,
        ha="center", fontproperties=font_bold.prop, color="#000000"
    )
    
    # Add subtitle
    fig.text(
        0.515, 0.942,
        subtitle,
        size=13,
        ha="center", fontproperties=font_bold.prop, color="#000000", fontweight='bold',
    )

    # Add credits
    CREDIT_1 = f"data: wyscout | values in: {value_display}\ndb: {num_players} {position_key} with {min_minutes} + min from 12 relevant leagues" 
   # CREDIT_2 = "wSwC: shooting relevant contributions\nwPwC: passing relevant contributions\nwAwC: attacking relevant contributions\nwDwC: defensive relevant contributions"
    CREDIT_3 = "reddit: u/ringokakiage | ringokakiage.wordpress.com"
    
    fig.text(
        0.125, 0.17, "Slice colors:", size=9,
        fontproperties=font_italic.prop, color="#000000",
        ha="left"
    )
    fig.text(
        0.125, 0.155, "Very below average (0-30%)", size=9,
        fontproperties=font_italic.prop, color="#a20e0e",
        ha="left"
    )
    fig.text(
        0.125, 0.14, "Below average (30-45%)", size=9,
        fontproperties=font_italic.prop, color="#d8580b",
        ha="left"
    )
    fig.text(
        0.125, 0.125, "Average (45-65%)", size=9,
        fontproperties=font_italic.prop, color="#f6d354",
        ha="left"
    )
    fig.text(
        0.125, 0.11, "Above average (65-80%)", size=9,
        fontproperties=font_italic.prop, color="#329999",
        ha="left"
    )
    fig.text(
        0.125, 0.095, "Excellent (80-90%)", size=9,
        fontproperties=font_italic.prop, color="#396892",
        ha="left"
    )
    fig.text(
        0.125, 0.08, "Top 5% (95%+)", size=9,
        fontproperties=font_italic.prop, color="#814a66",
        ha="left"
    )

    
    fig.text(
        0.905, 0.08, f"{CREDIT_1}\n{CREDIT_3}", size=9,
        fontproperties=font_italic.prop, color="#000000",
        ha="right"
    )

    # fig.text(
    #     0.12, 0.9, f"{CREDIT_2}", size=9,
    #     fontproperties=font_italic.prop, color="#000000",
    #     ha="left", bbox=dict(boxstyle="round",
    #                ec=(1., 0.5, 0.5),
    #                fc=(1., 0.8, 0.8),
    #                         )
    # )

    # Return the figure and axes
    return fig, ax

# Get the player info
player_info = (league, team, player, position) 

# Define the plot type (currently only metrics are supported)
plot_type = 'metrics'

# Create the pizza plot
result = create_pizza_plot(player_info, position_dfs, plot_type)

# Show the pizza plot
if result is not None:
    fig, _ = result
    st.pyplot(fig)
else:
    st.warning("Unable to create the pizza plot. Check the player data or input parameters.")

# Write the player info for more information
st.write(f"Player Info: {player_info}")
st.write(f"Position Key: {position}")
st.write(f"Player minutes: {chosen_player_minutes}")

# Write the explanation of the application
with st.expander('Como entender o funcionamento do aplicativo'):
    st.write('''
    Usando essa ferramenta, você pode gerar o radar de um jogador. Este radar tem como objetivo mostrar o desempenho de um jogador comparado com outros jogadores, trazendo em diferentes métricas autorais para auxiliar no scouting.\n
    Primeiro, escolha a liga, o time e o jogador desejado.\n
    Em seguida, escolha qual a posição e o mínimo de minutos jogados. Por fim, escolha se deseja comparar o jogador com outros jogadores da mesma liga ou com toda a base de dados.\n
    O radar gerado mostra o desempenho do jogador em comparação com outros jogadores da mesma posição, com valores em percentis. As cores das fatias do radar são baseadas no percentil do jogador em cada métrica.
    ''')

# Write the explanation of the metrics
with st.expander('O que são cada uma das métricas?'):
    st.write('''
    SwC, ou shooting na imagem, é a métrica que tem como objetivo entender qual foi o impacto dos chutes que determinado jogador teve em comparação com jogadores da mesma posição. A métrica foi confeccionada utilizando valores como chutes, chutes ao alvo, xG, diferença de gols e xG, entre outros.
    \n
    PwC, ou passing na imagem, é a métrica que tem como objetivo entender qual foi o impacto dos passes que determinado jogador teve em comparação com jogadores da mesma posição. A métrica foi confeccionada utilizando valores como passes progressivos, passes chave, passes para chutes, precisão de passes, entre outros.
    \n
    AwC, ou attacking na imagem, é a métrica que tem como objetivo entender qual foi o impacto das jogadas individuais ofensivas que determinado jogador teve em comparação com jogadores da mesma posição. A métrica foi confeccionada utilizando valores como dribles, avanços progressivos, duelos ofensivos, entre outros.
    \n
    DpwC, ou reactive defense na imagem, é a métrica que tem como objetivo entender qual foi o impacto defensivo reativo que determinado jogador teve em comparação com jogadores da mesma posição. A métrica foi confeccionada utilizando valores como duelos defensivos, desarmes (ajustado por posse), faltas, entre outros.
    \n
    DcwC, ou positional defense na imagem, é a métrica que tem como objetivo entender qual foi o impacto defensivo posicional que determinado jogador teve em comparação com jogadores da mesma posição. A métrica foi confeccionada utilizando valores como interceptações (ajustado por posse), bloqueios, recuperações de bola, entre outros.
    \n
    E, por último, Aerial impact é a métrica que tem como objetivo entender qual foi o impacto aéreo que determinado jogador teve em comparação com jogadores da mesma posição.
   
    ''')
