
import mome
import inspect
import os
import subprocess
import pyperclip
import json
import matplotlib.pyplot as plt
import glob
import momeutils



def extract_main_parts_with_ending_ngrams(transcription = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
    You are a transcription analyst with expertise in text processing assisting the user in identifying sections and their boundaries from transcriptions. In particular, you are expected to identify and title the main parts of a transcription and **extract** the last n-gram (the exact sequence, accurate on language, syntax, punctuation and capitalization ) for each section. 
    Answer in a JSON format as follows:
    ```json
    {{
    
        "titles" : [
            [
                "List of main parts as titles 0",
                "The extracted ending 5-gram for the section"
            ],
            [
                "List of main parts as titles 1",
                "The extracted ending 5-gram for the section"
            ],
            // add more items as needed...
        ]
    
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Transcription\n{}\n\n Extract main parts from the transcription and return a list of titles with their corresponding extracted ending 5-grams\n\n".format(icl_examples, transcription)}
    ]
    
    results = momeutils.parse_json(momeutils.ask_llm(messages, model = "pro"))
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return results["titles"]



def show_contents(transcription, titles_and_closing):  
    start_indexes = [0]
    end_indexes = []
    for i, (t, c) in enumerate(titles_and_closing):
        end_index = transcription.find(c)
        end_indexes.append(end_index)
        if i < len(titles_and_closing) - 1:
            start_indexes.append(end_index)
    
    # Calculate word counts
    word_counts = []
    for start, end in zip(start_indexes, end_indexes):
        section_text = transcription[start:end]
        word_count = len(section_text.split())
        word_counts.append(word_count)
    
    print('Start: {} \nEnd: {}'.format(start_indexes, end_indexes))
    # Plotting
    fig, ax = plt.subplots(figsize=(12, len(titles_and_closing) * 0.5))
    y_positions = range(len(titles_and_closing))
    bar_heights = 0.3

    for i, (start, end, title, word_count) in enumerate(zip(start_indexes, end_indexes, titles_and_closing, word_counts)):
        ax.barh(i, end - start, left=start, height=bar_heights, align='center', 
                alpha=0.8, label=f"{title[0]} ({word_count} words)")
    ax.set_yticks(y_positions)
    ax.set_yticklabels([t[0] for t in titles_and_closing])
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('Character Position in Transcription')
    ax.set_title('Span of Snippets in Transcription')

    # Add legend with word counts
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Sections (Word Count)")

    plt.tight_layout()
    plt.show()


def set_indexes(config):

    complete_structure = json.load(open(config['structure_path'])) 

    # collecting indexes 
    results = [{"title": s[0], 'closing': s[1], 'start_index': 0, 'end_index': 0} for s in complete_structure['structure']]
    start_index = 0 
    for i, s in enumerate(complete_structure['structure']):
        end_index = complete_structure['initial_content'].find(s[1])        
        results[i]['start_index'] = start_index
        results[i]['end_index'] = end_index

        start_index = end_index
    
    complete_structure['structure'] = results
    return complete_structure

def run_checks(config):

    structure = json.load(open(config['structure_path'])) 
    # checking if the indexes are correct

    for i,s in enumerate(structure['structure']):    
        if s['end_index'] < s['start_index']:
            if i < len(structure['structure']) -1:
                next_stage = structure['structure'][i+1]
                s['end_index'] = next_stage['start_index'] if next_stage['start_index'] > s['start_index'] else int((next_stage['end_index'] + s['start_index'])/2)
                # input(' Changed end index for {} to {}'.format(s['title'], s['end_index']))
            else:
                s['end_index'] = len(structure['initial_content'])
        elif s['start_index'] == -1: 
            prev_struct = structure['structure'][i-1]
            s['start_index'] = prev_struct['end_index'] if i > 0 else 0
        else: 
            print('Fine for {}'.format(s['title']))
    
    momeutils.crline(json.dumps(structure['structure'], indent = 4))    
    return structure

def to_graph(config):

    structure = json.load(open(config['structure_path']))
    vault_path = config['interactive_graph_path']

    mome.init_obsidian_vault(vault_path, exists_ok = True)
    node_seq = []
    node_seq.append(mome.add_node_to_graph(vault_path, 
                                           {"Recap": "```json\n{}\n```".format(json.dumps(structure['structure'], indent = 4)), 
                                            "Initial contents": structure['initial_content']},
                                           tags = ['anchor'], 
                                           name_override = mome.get_short_hash(structure['initial_content'], 15),
                                           use_hash = False))

    for i, s in enumerate(structure['structure']):
        node_seq.append(mome.add_node_to_graph(vault_path, 
                                               [s['title'], structure['initial_content'][s['start_index']:s['end_index']]], 
                                               parent_path = node_seq[-1], 
                                               name_override = "{}_{}".format(s['title'].lower().replace(' ', '_'), os.path.basename(node_seq[0]).split('.')[0]), 
                                               use_hash = False))
    

    
def get_base_structure(structure = None, initial_contents = None):
    return {"structure": structure, "initial_content": initial_contents}

def init_config_file(config_path): 
    config = {
        "base_contents_path": None, 
        "structure_path": None,
        "interactive_graph_path": os.path.join(os.path.dirname(__file__), 'interactive_graph'),
        "current_base_hash": None, 
        "operating_modules": None, 
        "clipboard_contents": momeutils.get_clipboard(),
    }

    with open(config_path, 'w') as f:
        json.dump(config, f, indent = 4)

def load_config(config_path, **kwargs):
    if not os.path.exists(config_path):
        init_config_file(config_path)
    with open(config_path, 'r') as f:
        config = json.load(f)
    nb_upates = 0 
    for k,v in kwargs.items():  
        if k in config.keys():
            nb_upates += 1
            config[k] = v
    
    if nb_upates > 0:
        momeutils.crline('Updated config file')
    save_config(config, config_path)
    
    return json.load(open(config_path))

def save_config(config, p ): 
    with open(p, 'w') as f:
        json.dump(config, f, indent = 4)

def init_contents(config_path, hash_length = 15): 

    with open(config_path, 'r') as f:
        config = json.load(f)
    if config['base_contents_path'] is None:
        tmp_path = os.path.join(os.path.dirname(__file__), '.contents_{}.txt'.format(mome.get_short_hash(config['clipboard_contents'], hash_length)))
        with open(tmp_path, 'w') as f:
            f.write(config['clipboard_contents'])
        config['base_contents_path'] = tmp_path
        momeutils.crline('Loading from clipboard and saving to {}'.format(tmp_path))
    
    current_hash = mome.get_short_hash(open(config['base_contents_path']).read(), hash_length)
    config['current_base_hash'] = current_hash
    config['structure_path'] = os.path.join(os.path.dirname(__file__), 'results_{}.json'.format(current_hash))
    
    return config
def save_current_structure(structure, config):
    with open(config['structure_path'], 'w') as f:
        json.dump(structure, f, indent = 4)
        
def initial_build(config_path, **kwargs):

    config = load_config(config_path, **kwargs)
    config = init_contents(config_path) # checks if using clipboard, saves to file and updates config
    save_config(config, config_path)

    base_content_path = config['base_contents_path']
    initial_contents = open(base_content_path).read()
    structure = get_base_structure(extract_main_parts_with_ending_ngrams(initial_contents), initial_contents)
    save_current_structure(structure, config)
    save_current_structure(set_indexes(config), config)
    save_current_structure(run_checks(config), config)

    to_graph(config)


def delete_hash(config_path): 
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    target_folder = config['interactive_graph_path']
    parent_node_to_delete = mome.select_file_in_folder(target_folder, target_tags = ['anchor'])
    mome.delete_node_dynasty(parent_node_to_delete)
    


if __name__ == "__main__":
    # Get the transcription from the clipboard
    transcription = open("/home/mehdimounsif/recordings/recording_FlorentRodolpheCIRClientEDF.txt").read()
    # structure = get_base_structure(extract_main_parts_with_ending_ngrams(transcription), transcription)
    
    # with open(os.path.join(os.path.dirname(__file__), 'results.json'), 'w') as f:
    #     json.dump(structure, f, indent = 4)
    structure = json.load(open(os.path.join(os.path.dirname(__file__), 'results.json')))
    structure = set_indexes(structure)
    print(json.dumps(structure['structure'], indent = 4))
    structure = run_checks(structure)   
    print(json.dumps(structure['structure'], indent = 4))

    to_graph(structure)