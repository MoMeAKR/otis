
import mome
import inspect
import os
import subprocess
import pyperclip
import json
import matplotlib.pyplot as plt
import glob
import momeutils
import otis_tools 


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


def show_contents(structure, save_path= None): 

    # Plotting
    fig, ax = plt.subplots(figsize=(12, len(structure) * 0.5))
    y_positions = range(len(structure))
    bar_heights = 0.3

    # for i, (start, end, title, word_count) in enumerate(zip(
    for i,s in enumerate(structure):
        start = s['start_index']
        end = s['end_index']
        word_count = s['nb_words']
        title = s['title']

        ax.barh(i, end - start, left=start, height=bar_heights, align='center', 
                alpha=0.8, label=f"{title[0]} ({word_count} words)")
    ax.set_yticks(y_positions)
    ax.set_yticklabels([s['title'] for s in structure])
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('Character Position in Transcription')
    ax.set_title('Span of Snippets in Transcription')

    # Add legend with word counts
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Sections (Word Count)")
    plt.tight_layout()
    if save_path is not None:
        plt.savefig(save_path)
    else: 
        plt.show()


def set_indexes(config):

    complete_structure = json.load(open(config['structure_path'])) 

    # collecting indexes 
    results = [{"title": s[0], 'closing': s[1], 'start_index': 0, 'end_index': 0, 'nb_words': 0} for s in complete_structure['structure']]
    start_index = 0 
    for i, s in enumerate(complete_structure['structure']):
        end_index = complete_structure['initial_content'].find(s[1])        
        results[i]['start_index'] = start_index
        results[i]['end_index'] = end_index + len(s[1])
        results[i]['nb_words'] = len(complete_structure['initial_content'][start_index:end_index].split())

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
        s['nb_words'] = len(structure['initial_content'][s['start_index']:s['end_index']].split())  
    
    
    momeutils.crline(json.dumps(structure['structure'], indent = 4))    
    return structure

def to_graph(config):

    structure = json.load(open(config['structure_path']))
    vault_path = config['interactive_graph_path']
    mome.init_obsidian_vault(vault_path, exists_ok = True)

    im_path = os.path.join(vault_path, 'contents_{}.png'.format(config['current_base_hash']))
    show_contents(structure['structure'], save_path = im_path)

    node_seq = []
    node_seq.append(mome.add_node_to_graph(vault_path, 
                                           {"Viz": "![[{}]]".format(os.path.basename(im_path)), 
                                            "Recap": "```json\n{}\n```".format(json.dumps(structure['structure'], indent = 4)), 
                                            "Results structure": "", 
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

def regen_graph(config_path, **kwargs):   
    config = load_config(config_path, **kwargs)
    to_graph(config)

def merge(config_path, **kwargs): 
    config = load_config(config_path, **kwargs)
    
    structure = json.load(open(config['structure_path']))['structure']

    min_, max_ = config['words_tolerance']
    proposed_merges = []
    for i, s in enumerate(structure): 
        if len(proposed_merges)> 0:
            if i <= max(proposed_merges[-1]):
                continue

        if i < len(structure) - 1:
            
            if s['nb_words'] < min_: 
                print('Checking snippet {}: {} - nb_words: {}'.format(i, s['title'], s['nb_words']))  
                total_words = s['nb_words'] 
                j = i
                while total_words < min_ and j < len(structure) - 1:
                    j += 1
                    total_words += structure[j]['nb_words']
                proposed_merges.append((i, j))
    
    accepted=  momeutils.uinput('Proposed_merges: {}'.format(proposed_merges))
    
    if accepted.strip().lower() == "y": 
        new_structure, idx_to_remove = do_merge(structure, proposed_merges, retitle = True)

        # clean_idx(idx_to_remove, config)
        delete_hash(config_path, parent_node_to_delete = os.path.join(config['interactive_graph_path'], '{}.md'.format(config['current_base_hash'])))

        structure = json.load(open(config['structure_path']))
        structure['structure'] = new_structure
        save_current_structure(structure, config)
        to_graph(config)

def do_merge(structure, proposed_merges, retitle = True): 

    new_structure = structure.copy()    
    to_drop = []
    for i, j in proposed_merges:
        if retitle:
            new_title = momeutils.basic_task('Combine those titles into a single concise yet representative one\nCurrent title to merge: {}'.format(' | '.join([s['title'] for s in structure[i:j+1]])))
            momeutils.crline("Updated title: {} --> New title: {}".format(' | '.join([s['title'] for s in structure[i:j+1]]), new_title))
        else:
            new_structure[i]['title'] = ' '.join([s['title'] for s in structure[i:j+1]])
        new_structure[i]['end_index'] = structure[j]['end_index']
        new_structure[i]['nb_words'] = sum([s['nb_words'] for s in structure[i:j+1]])

        to_drop.extend(list(range(i+1, j+1)))

    print('Dropping: {}'.format(to_drop))
    new_structure = [s for i, s in enumerate(new_structure) if i not in to_drop]
    return new_structure, to_drop
    
    
def get_base_structure(structure = None, initial_contents = None):
    return {"structure": structure, "initial_content": initial_contents}

def init_config_file(config_path): 
    config = {
        "base_contents_path": None, 
        "structure_path": None,
        "interactive_graph_path": os.path.join(os.path.dirname(__file__), 'interactive_graph'),
        "current_base_hash": None, 
        "operating_modules": None, 
        "apply_func" : None, # SHOULD BE UPDATED AT SOME POINT TO BE ABLE TO LOAD MORE ARBITRARILY 
        "clipboard_contents": momeutils.get_clipboard(),
        "words_tolerance": [160,300]
    }

    with open(config_path, 'w') as f:
        json.dump(config, f, indent = 4)

def load_config(config_path, **kwargs):
    if not os.path.exists(config_path):
        init_config_file(config_path)
    with open(config_path, 'r') as f:
        config = json.load(f)
    nb_updates = 0 
    for k,v in kwargs.items():  
        if k in config.keys():
            nb_updates += 1
            config[k] = v
            if k == "base_contents_path": 
                config['current_base_hash'] = mome.get_short_hash(open(kwargs['base_contents_path']).read(), 15)
                nb_updates += 1 

    if nb_updates > 0:
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


def delete_hash(config_path, **kwargs): 
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    target_folder = config['interactive_graph_path']
    if "parent_node_to_delete" in kwargs.keys():
        parent_node_to_delete = kwargs['parent_node_to_delete']
    else: 
        parent_node_to_delete = mome.select_file_in_folder(target_folder, target_tags = ['anchor'])
    link_sections = "\nLink result from ".join(["Links"] + mome.get_node_section(parent_node_to_delete, target_section = 'Results structure').split('\n')).split('\n')

    mome.delete_node_dynasty(parent_node_to_delete, link_section = link_sections)
    
    im_path = os.path.join(target_folder, 'contents_{}.png'.format(os.path.basename(parent_node_to_delete).split('.')[0]))
    if os.path.exists(im_path): 
        os.remove(im_path)


def apply(config_path, **kwargs): 
    config = load_config(config_path, **kwargs)
    target_dynasty = mome.collect_dynasty_paths(os.path.join(config['interactive_graph_path'], '{}.md'.format(config['current_base_hash'])))
    if config['apply_func'] is None:
        momeutils.crline('No apply function specified')
        return 
    
    func = getattr(otis_tools, config['apply_func'])

    # Enhancing the root node with the Result section with the function name for downstream tracking (or deletion)
    root_node = os.path.join(config['interactive_graph_path'], '{}.md'.format(config['current_base_hash']))
    current_contents = mome.get_node_section(root_node, target_section = 'Results structure')
    if current_contents is None:
        current_contents = ""
    current_contents = current_contents.strip().split('\n')
    current_contents.append(config['apply_func'].strip())

    mome.update_section(root_node, 'Results structure', '\n'.join(current_contents))
    

    for node in target_dynasty:
        contents = mome.get_node_section(node)
        out = func(contents)
        r_node = mome.add_node_to_graph(config['interactive_graph_path'], "That's the results {}".format(out), 
                                        name_override = 'result_{}_{}'.format(config['apply_func'], os.path.basename(node).split('.')[0]),
                                        tags = ['results_{}'.format(config['apply_func'])]) 
        mome.enhance_links(node, os.path.basename(r_node).split('.')[0], link_section = 'Link result from {}'.format(config['apply_func']))
        
        
        

if __name__ == "__main__":

    import shutil
    # copy the interactive graph folder to a safe 
    tp = json.load(open("/home/mehdimounsif/.local/bin/otis_config.json"))['interactive_graph_path']
    safe=  "/home/mehdimounsif/Codes/my_libs/otis/interactive_graph_backup"
    if not os.path.exists(safe):
        shutil.copytree(tp, safe)
    else: 
        print('Loading from safe')
        shutil.rmtree(tp)
        shutil.copytree(safe, tp)

    apply("/home/mehdimounsif/.local/bin/otis_config.json") 
    input('ok ? ')
    delete_hash("/home/mehdimounsif/.local/bin/otis_config.json")

