import copy 
import os
import json
import momeutils
import re
import glob
import shutil
import inspect
import mome
import subprocess



def generate_paragraph_subcontents(structured_text = None, nb_paragraphs = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
You are an AI assistant expert in text analysis assisting the user in preparing accurate and efficient guidelines for textual content generation. Concretely, based on provided high-level control structure, you are expected generate {n} paragraph guidelines in a list of targeted subcontents (each element in the list will be used to produce a separate paragraph).

The provided controls can include: 
* Hierarchy location: tells you where the current paragraph fits in the broader context
* High-level context: What the current section is 
* Content: The main content of the paragraph(s) --> the message we want to convey
* Things said before: What was mentioned before in the section (if anything). This way, you can build upon more complex and sophisticated ideas and reuse the introduced concepts
* Where this is going: The following parts of the current section (if any). If provided, use those  as a reference to create a coherent and logical flow of ideas and ensure smooth transitions between paragraphs
* Number of paragraphs: The number of paragraphs you should generate for the provided contents
* Examples: Examples that the user expects for further illustrating the content (optional)
* Specific viewpoint: A specific viewpoint that the user wants to be considered (optional)
* References: References that the user wants to be included (optional)
* Visuals: Visuals that the user wants to be included (optional)

             
Answer in a JSON format as follows:
    ```json
    {{
    
        "list_of_contents" : [
{p_desc}
        ]
    
    }} 
    ```
    """.format(n = nb_paragraphs, 
               p_desc = ",\n".join(["High-level guidelines (a sentence or two) for paragraph {}".format(i) for i in range(nb_paragraphs)]))}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Text generation controls \n{}\n\nGiven the provided controls, produce {} grounded paragraphes guidelines under the key 'list_of_contents' that will be used for downstream generation.\n\n".format(icl_examples, structured_text, nb_paragraphs)}
    ]
    
    # results = momeutils.parse_json(momeutils.ask_llm(messages, model = "g4o"))
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = momeutils.safe_llm_ask(messages, model = 'g4o') 
    momeutils.crprint(json.dumps(results, indent = 4))
       
    
    return results["list_of_contents"]

def determine_text_relevance_to_section(text = None, hierarchy = None, target_section = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
    You are an AI assistant with expertise in Natural Language Processing, assisting the user in organizing textual information within a hierarchical structure. Concretely, you are expected to assess the relevance of a given text snippet to a specific section, considering the provided document hierarchy. 
    Answer in a JSON format as follows:
    ```json
    {{
        "target_section_parent" : "The parent section of the target section",
        "short_rationale" :"A brief explanation of why the considered text makes sense (or not) regarding the hierarchy", 
        "score" : "A score ranging from 0 to 10 indicating the relevance of the provided text to the target section"
    
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Text\n{}\n\n Hierarchy\n{}\n\n Target Section\n{}\n\nGiven a text snippet, a document hierarchy, and a target section, determine the relevance of the text to the target section and return a score between 0 and 10, with 10 indicating perfect relevance.\n\n".format(icl_examples, text, hierarchy, target_section)}
    ]

    parseable = False
    while not parseable: 
        initial_answer, parseable, results = momeutils.safe_llm_ask(messages, model = 'g4o') 
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return results["score"]

def paragraph_writer(paragraph_template = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    

    messages = [
            {"role": "system", "content": """
    You are a writing assistant with expertise in producing well-structured and coherent paragraphs. You are expected to use the provided template and precisely follow the guidelines. 
    Answer in a JSON format as follows:
    ```json
    {{
        "results":{{
{result}
             }}
    }} 
    ```
    """.format(result = ",\n".join(["\"paragraph_{i}\": \"Paragraph {i} based on the provided template and critical elements.\"".format(i = i) for i in range(len(paragraph_template))]))},
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Paragraph Template\n{}\n\nUse the provided paragraph template to produce a well-structured and coherent text under the key 'result'.\n\n".format(icl_examples, paragraph_template)}
    ]
    momeutils.dj(messages)
    results = momeutils.parse_json(momeutils.ask_llm(messages, model = "g4o"))
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return results["result"]

def paragraph_writer2(paragraph_template = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    

    messages = [
            {"role": "system", "content": """
You are a writing assistant with expertise in producing well-structured and coherent contents. You are expected to use the provided high-level layout and generate clear, well-structured and convincing text. 
Answer in a JSON format as follows:
    ```json
    {{
        "contents":"Your resulting contents"
    }} 
    ```
    """},
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n High-level layout\n{}\n\nUse the provided layout template to produce a well-structured and coherent text under the key 'contents'. To prevent formatting issues, use '\\n' in your answer to represent line breaks \n\n".format(icl_examples, "\n* ".join([''] + paragraph_template))}
    ]

    parseable = False
    while not parseable: 
        initial_answer, parseable, results = momeutils.safe_llm_ask(messages, model = 'g4o') 
        # print(initial_answer)
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return results["contents"]

def paragraph_writer_enhanced(paragraph_template = None): 

    icl_examples = momeutils.load_icl(inspect.currentframe())
    
    messages = [
            {"role": "system", "content": """
You are a writing assistant with expertise in producing well-structured and coherent paragraphs. You are expected to generate contents based on a provided template. 
Specifically, here are some controls that will inform your produced text: 
* Hierarchy location: tells you where the current paragraph fits in the broader context
* High-level context: What the current section is 
* Content: The main content of the paragraph(s) --> the message we want to convey
* Things said before: What was mentioned before in the section (if anything). This way, you can build upon more complex and sophisticated ideas and reuse the introduced concepts
* Where this is going: The following parts of the current section (if any). If provided, use those  as a reference to create a coherent and logical flow of ideas and ensure smooth transitions between paragraphs
* Number of paragraphs: The number of paragraphs you should generate for the provided contents
* Examples: Examples that the user expects for further illustrating the content (optional)
* Specific viewpoint: A specific viewpoint that the user wants to be considered (optional)
* References: References that the user wants to be included (optional)
* Visuals: Visuals that the user wants to be included (optional)
                 
Answer in a JSON format as follows:
    ```json
    {{
        "paragraphs_overlay": [what the first sub-paragraph is about, what the second sub-paragraph is about, ...], // if nb_paragraphs > 1
        "result" : "The generated paragraph based on the provided template and critical elements."
    }}
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Paragraph Template\n{}\n\nUse the provided paragraph template to produce a well-structured and coherent paragraph under the key 'result'.\n\n".format(icl_examples, paragraph_template)}
    ]
    
    results = momeutils.parse_json(momeutils.ask_llm(messages, model = "g4o"))
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return results["result"]


def simple_extract(sample_text = None, sections = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    
    messages = [
            {"role": "system", "content": """
You are an expert annotator assisting the user in structuring text. You will be provided with a text and a list of sections (for an global perspective).  
Your task is to identify and sum up how the root text could fill each target section, while being mindful of the broader context. If nothing matches, answer with 'null'
Answer in a JSON format as follows:
    ```json
    {{
{sections}
    }} 
    ```
    """.format(sections = "\n".join(['"{sectionf}": What could fill the **{section}** subsection, based on the provided context",'.format(sectionf = section.lower().strip().replace(' ', "_"), section = section) for section in sections]))}, 
     
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Root text (serving as a knowledge repository)\n{}\n\n Sections\n{}\n\nGiven the root text and a list of sections, sum up some elements from the root text that could serve as justifications or supporting information for our section of interest (feel free to rephase instead of simply copy pasting things out). Try and be accurate and mindful of other sections, that is, not all content must be used and if nothing relates to the current elements, please use null.\n\n".format(icl_examples, sample_text, sections)}
    ]

    results = momeutils.parse_json(momeutils.ask_llm(messages, model = "g4o"))
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return  results


def init_config_file(config_path): 
    config = {
        "base_knowledge_path": os.path.join(os.path.dirname(__file__), 'sample_ainimals.txt'),
        "current_hash": None,
        "structure_path": os.path.join(os.path.dirname(__file__), 'sir_structure'),
        "interactive_graph_path": os.path.join(os.path.dirname(__file__), 'sir_interactive_graph'),
        "report_structure": {
            "operation_topic" : ['overview', {'issues_with_different_methods': ["method_A", "method_B"]}],
            "technical_justification": ["related works and their limitation", "why we should go in the direction we chose"], 
        },
        "focus_node": None, 
        "last_nodes_added": [],
        "user_instruction" : None, 
        "results_path": None, 
        "report_path": os.path.join(os.path.dirname(__file__), 'reports'),
        "control_key": None, 
        "control_contents": "", 
        "inadequate_contents": None, 
        "non_filled": None, 
        "paragraph_parameter": None, 
        "paragraph_parameter_content": None
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
            # print(k, v)
            nb_updates += 1
            config[k] = v

    if not "focus_node" in kwargs.keys(): 
        momeutils.crline('Loading focus node from active node')
        config['focus_node'] = mome.get_active_node(config['interactive_graph_path'])
        nb_updates += 1

    if nb_updates > 0:
        momeutils.crline('Updated config file')
    save_config(config, config_path)
    
    return json.load(open(config_path))

def save_config(config, p ): 
    with open(p, 'w') as f:
        json.dump(config, f, indent = 4)

def format_dynasty(dynasty, keep_path = False):
    # recursive function that scrolls through the dynasty (path, children) and each path is rewritten as os.path.basename(path)
    # and the children are recursively formatted
    p = os.path.basename(dynasty['path']).split('.')[0]
    formatted = {"path": dynasty['path'] if keep_path else p,
                  "name":  tmp_key_formatting(p.split('_')[-2], up_ = True) if '_' in p else p, 
                  "children": []}
    if len(dynasty['children']) > 0:
        for child in dynasty['children']:
            formatted['children'].append(format_dynasty(child, keep_path=keep_path))

    return formatted

def formatted_path_to_children(dynasty, children): 
    result= path_to_children(dynasty, children)
    root_name = result[0]
    # result[0] = 'Root'
    cleaned_result = ['Root']
    for i, r in enumerate(result[1:]):
        cleaned_result.append(r.split('_')[-2])
    return cleaned_result


def path_to_children(dynasty, target_children):

    # provided the full dynasty from the root, it returns the sequence of parents leading to the target_children
    if dynasty['path'] == target_children:
        return [dynasty['path']]
    else:
        for child in dynasty['children']:
            result = path_to_children(child, target_children)
            if result:
                return [dynasty['path']] + result



def format_section_title(s):
    return "".join([w.capitalize() for w in s.replace('_', ' ').lower().strip().split()])

def gf_all(v, show_structure = False):
    if show_structure: 
        return [[gf(vv), 'paragraph' if isinstance(vv, str) else 'section'] for vv in v]  
    return [gf(vv) for vv in v]

def gf(v): 
    """
    get first value, whichever type it is 
    """
    if isinstance(v, list): 
        return v[0]
    elif isinstance(v, dict):
        return list(v.keys())[0]
    elif isinstance(v, str): 
        return v
    else: 
        raise TypeError('Unrecognized type for gf --> v type: {}'.format(type(v)))




def create_nodes_recursively(root_hash, graph_folder, structure, parent_path=None, level=0, part=0, parent_hash=None):
    for key, value in structure.items():
        if isinstance(value, list):
            # Create the current node

            node_name = f"lvl{level}_part{part}_{format_section_title(key)}_{parent_hash}" if parent_hash else f"{parent_hash}"
            current_hash = mome.get_short_hash(node_name, 15)

            node_contents = {
                # "Base contents": momeutils.j_deco(setup_base_contents_from_hls(value)),
                "Control center": momeutils.j_deco(setup_control_center_from_hls(value)),
                "Section structure": momeutils.j_deco(setup_section_structure_from_hls(value)),
                "Results": ""
            }

            # Update control center with the structure

            # Update base contents 

            created_node_path = mome.add_node_to_graph(
                graph_folder=graph_folder,
                contents=node_contents,
                parent_path=parent_path,
                tags=["sub_" * level + "section"],
                name_override=node_name,
                use_hash=False
            )
            

            # THESE ARE FOR AUTOMATICALLY FILLING THE PARAGRAPH CONTROLS 
            section_population = []
            section_depopulation = gf_all(value)[1:]#[gf(v) for v in value][1:]

            # Recursively create child nodes
            for i, item in enumerate(value):
                
                if isinstance(item, dict):
                    create_nodes_recursively(root_hash, graph_folder, item, created_node_path, level + 1, i, current_hash)
                else:
                    # Create leaf node

                    leaf_name = f"lvl{level + 1}_part{i}_{format_section_title(item)}_{current_hash}"
                    # full_dynasty_formatted = format_dynasty(mome.collect_dynasty_paths(os.path.join(graph_folder, root_hash + ".md"), include_root=True, preserve_hierarchy=True))
                    # print(full_dynasty_formatted)
                    # print(leaf_name)
                    # input(' ok ')
                    # hierarchy_location = path_to_children(full_dynasty_formatted, leaf_name)
                    high_level_context = key # global view 
                    # print(leaf_name, key)
                    things_said_before = section_population if len(section_population) >0 else None,
                    where_this_is_going = section_depopulation if len(section_depopulation) > 0 else None

                    leaf_contents = {
                        
                        "Control center": momeutils.j_deco(initiate_control_center(
                                                                                hierarchy_location = 'to_fill',
                                                                                high_level_context = high_level_context,
                                                                               content = f"We gotta talk about {item}", 
                                                                               things_said_before = things_said_before, 
                                                                               where_this_is_going = where_this_is_going,)),
                        "Results": ""
                    }
                    mome.add_node_to_graph(
                        graph_folder=graph_folder,
                        contents=leaf_contents,
                        parent_path=created_node_path,
                        # tags=["sub_" * (level + 1) + "section"],
                        tags = ['results'],
                        name_override=leaf_name,
                        use_hash=False
                    )
                    section_population.append(item)
                    if len(section_depopulation)>0: 
                        section_depopulation.pop(0)
        else:
            # Handle other cases if necessary
            pass

def make_graph(config_path=None, **kwargs):
    config = load_config(config_path, **kwargs)
    mome.init_obsidian_vault(config['interactive_graph_path'], exists_ok=False)

    structure = {
    "Operation Topic": ['Overview',
        {'Limitations Of Our Previous Perspective And What Is Wrong With Other Methods': [
                "Focus On Local Problems Instead Of Systemic Solutions",
                "Automated Processing Of unstructured data",
                "Knowledge Management"
        ]
        },
        "High-level Vision Of What We Did"
    ],
    "Technical Justification": [
        "Test"
    ],
    "What We Actually Did": [
        "Test"
    ],
    "Conclusion": [
        "Test"
    ]
    }

    config['report_structure'] = structure

    # Root id
    base_hash = mome.get_short_hash("hello", 15)  # TMP
    
    # Create root node
    root_contents = {"Control center": momeutils.j_deco(setup_control_center_from_hls(structure)),
                     "Section structure": momeutils.j_deco(setup_section_structure_from_hls(structure)),
                     "Results": ""}
    root_node_path = mome.add_node_to_graph(
        graph_folder=config['interactive_graph_path'],
        contents=root_contents,
        parent_path=None,
        tags=["root"],
        name_override=base_hash,
        use_hash=False
    )

    config['current_hash'] = base_hash
    config['results_path'] = os.path.join(os.path.dirname(config['report_path']), "results", f"results_{base_hash}.json")

    # Create nodes recursively
    create_nodes_recursively(config['current_hash'], config['interactive_graph_path'], structure, root_node_path, level=0, part=0, parent_hash=base_hash)
    save_config(config, config_path)

def get_control_center(node): 
    return momeutils.parse_json(mome.get_node_section(node, "Control center"))  

def get_section_structure(node):
    return momeutils.parse_json(mome.get_node_section(node, "Section structure"))


def propagate(config_path = None, **kwargs): 


    inadequate_contents, non_filled = do_propagate(config_path, **kwargs)
    config = load_config(config_path, **kwargs)
    momeutils.crline("{}".format(json.dumps({"inadequate_contents": inadequate_contents, "non_filled": non_filled}, indent = 4)))
    config['inadequate_contents'] = inadequate_contents
    config['non_filled'] = non_filled
    save_config(config, config_path)

def do_propagate(config_path=None, **kwargs):
    config = load_config(config_path, **kwargs)
    full_dynasty_formatted = format_dynasty(mome.collect_dynasty_paths(os.path.join(config['interactive_graph_path'], config['current_hash'] + ".md"), include_root=True, preserve_hierarchy=True))
    focus_node_path = os.path.join(config['interactive_graph_path'], config['focus_node'] + ".md")
    control_center = get_control_center(focus_node_path)
    links = mome.get_node_links(focus_node_path)
    inadequate = {}
    non_filled = {}
    for i, (k,l) in enumerate(zip(control_center.keys(), links)):
        link_path = os.path.join(config['interactive_graph_path'], l + ".md")
        if control_center[k]['template'] == "direct": 
            link_control_center = get_control_center(os.path.join(config['interactive_graph_path'], l + ".md"))

            before = list(control_center.keys())[:i]
            before = before if len(before) > 0 else None
            after = list(control_center.keys())[i+1:]
            after = after if len(after) > 0 else None

            
            hierarchy_location = formatted_path_to_children(full_dynasty_formatted, l)

            link_control_center = update_existing_structure(link_control_center, 
                                                            hierarchy_location = hierarchy_location,
                                                            content = control_center[k]['user_instruction'], 
                                                            things_said_before = before,
                                                            where_this_is_going = after)
            mome.update_section(link_path, 
                                "Control center",
                                momeutils.j_deco(link_control_center))
        elif control_center[k]['template'] == "default": 
            # insert in initial contents

            momeutils.crline('Updating section structure in {}'.format(l))
            section_structure = momeutils.parse_json(mome.get_node_section(link_path, "Section structure"))
            section_structure = update_existing_structure(section_structure, 
                                                          initial_contents = control_center[k]['user_instruction'])
            mome.update_section(link_path,
                                "Section structure", 
                                momeutils.j_deco(section_structure))
            if not section_structure['subs_titles'] == ['To Fill']:
                leftovers = pour_info(config_path, focus_node = l)
                # momeutils.dj({"Focus node": config['focus_node'], 
                #               "L": l, 
                #               "Leftovers": leftovers})
                # inadequate[config['focus_node']] = leftovers
                inadequate[l] = leftovers
                # momeutils.dj({"leftovers": leftovers, 
                #             "inadequate": inadequate})
                # inadequate[l] = do_propagate(config_path, focus_node = l)
                prop_results = do_propagate(config_path, focus_node = l)
                inadequate[l] += prop_results[0]
                non_filled[l] = prop_results[1]
            else: 
                non_filled[l] = 'to_fill'
    return inadequate, non_filled

def collect_hierarchy_to_focus_node(config):
    return collect_hierarchy_to_children(config, config['focus_node'])
     
def collect_hierarchy_to_children(config, target_node_path): 
    root_path = os.path.join(config['interactive_graph_path'], config['current_hash'] + ".md")
    hierarchy = formatted_path_to_children(format_dynasty(mome.collect_dynasty_paths(root_path, include_root=True, preserve_hierarchy=True)), target_node_path)
    return hierarchy


def add_default_hierarchical_node(focus_node_contents, node_name, parent_path = None): 
    control_center = focus_node_contents['control']
    lvl, part, name, hash_ = split_node_for_info(focus_node_contents['path'])
    
    
    current_node_key = tmp_key_formatting(node_name.split('_')[-2], up_ = True)
    new_control_center = setup_control_center([["To Fill", control_center[current_node_key]['template']]])
    new_section_structure = setup_section_structure(initial_contents = "Empty", subs_titles = ['To Fill'])
    node_contents = {"Control center": momeutils.j_deco(new_control_center), 
                    "Section structure": momeutils.j_deco(new_section_structure), 
                    "Results": ""} 
    tags = ["sub_"*(lvl+1) + "section"]

    return mome.add_node_to_graph(
        graph_folder=os.path.dirname(focus_node_contents['path']),
        contents=node_contents,
        parent_path=parent_path, # putting it to None and adding it later otherwise it gets added at the end 
        tags = tags, 
        name_override= node_name,
        use_hash=False
    )

def add_default_result_node(focus_node_contents, node_name, parent_path = None): 
    new_control_center = initiate_control_center()
    node_contents = {"Control center": momeutils.j_deco(new_control_center), 
                    "Results": ""}
    tags = ['results']

    return mome.add_node_to_graph(
        graph_folder=os.path.dirname(focus_node_contents['path']),
        contents=node_contents,
        parent_path=parent_path,
        tags=tags,
        name_override=node_name,
        use_hash=False
    )


def check_children_node_existence(config, focus_node_contents): 

    control_center = focus_node_contents['control']
    lvl, part, name, hash_ = split_node_for_info(focus_node_contents['path'])
    focus_node_hash = mome.get_short_hash(momeutils.bn(focus_node_contents['path']), 15)

    # Constructing node name and creating node if currently missing 
    for i,k in enumerate(control_center.keys()): 
        node_name = f"lvl{lvl+1}_part{i}_{k.replace(' ', '')}_{focus_node_hash}"
        node_path = os.path.join(os.path.dirname(focus_node_contents['path']), node_name + ".md")
        
        add_children_paragraph = False 
        
        if not os.path.exists(node_path):
            if control_center[k]['template'].strip() == "default": 
              
                input('about to hierarchical add {}'.format(node_name))
                added_node = add_default_hierarchical_node(focus_node_contents, node_name)
                add_children_paragraph = True 
            else:
                input('about to result add {}'.format(node_name))
                added_node = add_default_result_node(focus_node_contents, node_name)
         

            # Since the node is added, assume it is user validated --> Add it to links 
            mome.add_link_at_position(focus_node_contents['path'], node_name , i)

            # IF THE NODE IS A SECTION (HIERARCHY) NODE, 
            # WE AUTOMATICALLY CREATE A PLACEHOLDER CHILD TO ENSURE CORRECT DOWNSTREAM USAGE OF STRUCTURE
            if add_children_paragraph: 
                new_section_structure = get_section_structure(added_node)
                section_hash = mome.get_short_hash(node_name, 15)
        
                p_name = f"lvl{lvl+2}_part0_{new_section_structure['subs_titles'][0].replace(' ', '')}_{section_hash}"
            
                input('FOllowing hierachical add, adding result node {}'.format(p_name))
                add_default_result_node(focus_node_contents, p_name, parent_path = added_node)

                current_dynasty = format_dynasty((mome.collect_dynasty_paths(focus_node_contents['path'], include_root=True, preserve_hierarchy=True)), keep_path= True)
                node_index = [i for i, c in enumerate(current_dynasty['children']) if c['path'] == node_path][0]
                current_dynasty['children'][node_index] = {"path": node_path, "children": [{"path": os.path.join(os.path.dirname(node_path), p_name + ".md"), "children": []}]}
                config['report_structure'] = update_report_structure(config, current_dynasty, focus_node_contents['path'])


def update_children_node_state(config, focus_node_contents):
    """
    For each children, checks if the template matches 
    If there are changes, 
        * Removes the dynasty, 
        * Adds the relevant node (ideally, node contents should be somehow kept )
        * Updates the config report structure accordingly
    """

    control_center = focus_node_contents['control']
    lvl, part, name, hash_ = split_node_for_info(focus_node_contents['path'])
    focus_node_hash = mome.get_short_hash(momeutils.bn(focus_node_contents['path']), 15)
    for i, k in enumerate(control_center.keys()): 
        # IS THERE DISCREPANCY BETWEEN TEMPLATE AND ACTUAL NODE TYPE
        # VARIOUS WAYS TO CHECK -> FIRST APPROXIMATION USING TEMPLATE SECTIONS 
        user_request = control_center[k]['template'].strip().lower()
        node_path = os.path.join(os.path.dirname(focus_node_contents['path']), f"lvl{lvl+1}_part{i}_{k.replace(' ', '')}_{focus_node_hash}.md")
        node_type = 'default' if mome.check_section(node_path, "Section structure") else 'direct'
        
        # ADDING THE NODE 
        if node_type != user_request: 
            clean_dynasty(node_path, include_root = True)
            if user_request == "direct": 
                child_node_name = f"lvl{lvl+1}_part{i}_{k.replace(' ', '')}_{focus_node_hash}"  
                add_default_result_node(focus_node_contents, child_node_name)
            elif user_request == "default":
                child_node_name = f"lvl{lvl+1}_part{i}_{k.replace(' ', '')}_{focus_node_hash}"
                add_default_hierarchical_node(focus_node_contents, child_node_name)
            else: 
                raise ValueError(f'Unrecognized template type {user_request}')

    return 


    
def pour_info(config_path=None, **kwargs):
    config = load_config(config_path, **kwargs)

    focus_node = get_focus_node(config)
    focus_node_path = focus_node['path']

    hierarchy = collect_hierarchy_to_focus_node(config)
    section_structure = focus_node['structure']
    control_center = focus_node['control']
       
    # Ensuring node existence and managing report_structure
    check_children_node_existence(config, focus_node)
    update_children_node_state(config, focus_node)
    
    full_hierarchy = format_dynasty(mome.collect_dynasty_paths(os.path.join(config['interactive_graph_path'], config['current_hash'] + ".md")
                                                , include_root = True, preserve_hierarchy = True))
    # test = determine_text_relevance_to_section(text = section_structure['initial_contents'],
    #                                            hierarchy=json.dumps(full_hierarchy, indent = 4), 
    #                                            target_section=os.path.basename(focus_node_path).split('.')[0])
    
    leftovers = []
    results = simple_extract(sample_text = section_structure['initial_contents'], 
                             sections = section_structure['subs_titles'],)
    for k,v in results.items():
        if v is None or v.strip().lower() == "null": 
            leftovers.append(k)
    

    for i, (s,k) in enumerate(zip(section_structure['subs_titles'], results.keys())): 
        control_center[s]['user_instruction'] = results[k]
        
        if k in leftovers: 
            p = "Consider the following user-provided text: **{}**\n\nWe were trying to identify content for a section named {} and containing the following subsections {}. \n\nSpecifically, focus is on {}.Here is its positionning in the document hierarchy: \n{}\n\nIn the initial pass, it was deemed that the user-provided text did not contain relevant information to the target section. Based on your expert knowledge, suggest meaningful and insightful contents, topic or concepts that could enhance the current guidelines ? Your answer must go directly to the specifics (aka, directly provide your suggestions, avoid starting with unnecessary 'To enhance guidelines, blabla')".format(section_structure['initial_contents'], config['focus_node'].split('_')[-2], "\n*".join([''] + section_structure['subs_titles']), s, " ".join(["\n" + "\t" * i +"* " + h for i, h in enumerate(hierarchy)]))
            # input(p)
            control_center[s]['model_suggestion'] = momeutils.basic_task(p, model = 'g4o')
        # Add additional details here
    
    # updating sections 
    mome.update_section(focus_node_path, "Control center", momeutils.j_deco(control_center))

    save_config(config, config_path)
    return leftovers

def push_specific_parameter(config_path= None, **kwargs): 
    config= load_config(config_path, **kwargs)
    param_key = config['paragraph_parameter']
    param_content = config['paragraph_parameter_content']
    focus_node = get_focus_node(config)

    # collect all children leaf nodes 
    if is_leaf(focus_node['path']):
        target_children = [focus_node['path']]
    else: 
        
        target_children = collect_all_compilable_children(focus_node_path=focus_node['path'])
    for c in target_children: 
        control_center = get_control_center(c)
        p = "In the context of automated long-form text generation, we are looking to enhance the current leaf paragraph with a {}. The initial (fixed) context is described by the following parameters: \n{}\n\nFrom a high-level standpoint, overlooking multiple paragraph, the user has requested the following content to be included \n{}\n\nBased on the context, is the user provided input relevant or should it be kept for other places ? Answer with a short rationale and then conclude with an integer score from 0 to 10, (10 being perfect fit).".format(
            param_key, json.dumps(control_center, indent = 4), "{} --> {}".format(param_key, param_content))
        # input(p)
        print('Considering node: {}'.format(c))
        result = momeutils.basic_task(p, model = 'g4o')


def enhance_control_key(config_path=None, **kwargs):
    config = load_config(config_path, **kwargs)
    control_key = config['control_key']
    control_contents = config['control_contents']
    
    focus_node = get_focus_node(config)
    section_structure = focus_node['structure'] 
    control_center = focus_node['control']


    if not control_key.strip().lower() in [c.lower().strip() for c in control_center.keys()]:
        raise ValueError(f"Control key {control_key} not found in control contents")
    key_id = [k for k in control_center.keys() if k.lower().strip() == control_key.lower().strip()][0]
    p = "Initial complete content before split: {}\n\nTarget section: {}\n\nInitial content assigned to section: {}\n\nUser request: {}\n\nEnhance the Initial content assigned to section taking into account the global context and with particular attention to the user request.".format(section_structure['initial_contents'],
                                                     control_key, control_center[key_id], control_contents)
    out = momeutils.basic_task(p, model = "g4o")
    control_center[key_id]['user_instruction'] = out
    mome.update_section(focus_node['path'], "Control center", momeutils.j_deco(control_center))
    save_config(config, config_path)   



def more_contents(config_path = None, **kwargs):
    config = load_config(config_path, **kwargs)

    focus_node_path = os.path.join(config['interactive_graph_path'], config['focus_node'] + ".md")
    if config['user_instruction'] is not None and config['user_instruction'].strip() != '': 
        hierarchy = collect_hierarchy_to_focus_node(config)
        section_structure =get_section_structure(focus_node_path) 
        subs = get_section_structure(focus_node_path)['subs_titles']
        p = "As an efficient AI writing assistant, you are to provide insightful complementary ideas to the user based on the following information. \n Section location in the document hierarchy : \n{}\n Focus section is {}\n Subsections in this section are: \n{}\n\n The user has provided the following initial text: \n{}\n\nFinally, the user has also provided the following instruction: {}\n\nBased on this global view, rewrite/expand/enhance the initial provided text taking into account the additional instruction.".format("\n".join(["\t" + h for h in hierarchy]), config['focus_node'].split('_')[-2], "\n".join(["\t* " + s for s in subs]), section_structure['initial_contents'], config['user_instruction'])
        out = momeutils.basic_task(p, model = 'g4o')
        valid = momeutils.u_valid()
        if valid: 
            section_structure = update_existing_structure(section_structure, initial_contents = out)  
            mome.update_section(focus_node_path, "Section structure", momeutils.j_deco(section_structure))
    save_config(config, config_path)  
            

def is_leaf(current_node, target_tag = "results"): 
    tags= mome.get_file_tags(current_node)
    return target_tag in tags

def collect_all_compilable_children(focus_node_path, target_tag = ["results"]):
    node_dynasty = mome.collect_dynasty_paths(focus_node_path, include_root=False, preserve_hierarchy=False)
    _, result_nodes = mome.collect_node_contents(os.path.dirname(focus_node_path), tags = target_tag, return_paths = True)
    to_compile = [n for n in node_dynasty if n in result_nodes]
    return to_compile

def compile(config_path=None, **kwargs):
    config = load_config(config_path, **kwargs)
    focus_node_path = os.path.join(config['interactive_graph_path'], config['focus_node'] + ".md")
    if is_leaf(focus_node_path): 
        to_compile = [focus_node_path]
    else: 
        to_compile = collect_all_compilable_children(focus_node_path)
        # node_dynasty = mome.collect_dynasty_paths(focus_node_path, include_root=False, preserve_hierarchy=False)
        # _, result_nodes = mome.collect_node_contents(config['interactive_graph_path'], tags = ['results'], return_paths = True)
        # to_compile = [n for n in node_dynasty if n in result_nodes]
    print("\n* ".join([''] + [os.path.basename(n).split('.')[0] for n in to_compile]))
    

    # RUNNING THE ACTUAL COMPILATION
    print('You forgot to uncomment' *20)
    compilation_results = json.load(open('tmp.json'))
    # compilation_results = {}
    # for i, c in enumerate(to_compile): 

    #     # COMPILE RETURNS A DICT
    #     current_result = compile_node(c)
    #     result_key = os.path.basename(c).split('.')[0].split('_')[-2]
    #     lvl = int(os.path.basename(c).split('.')[0].split('_')[0].replace('lvl', ''))
    #     part = int(os.path.basename(c).split('.')[0].split('_')[1].replace('part', ''))
    #     # ADDING A KEY TO KEEP TRACK OF THE LEVEL OF THE NODE (SECTION, SUBSECTION, SUBSUBSECTION...)
    #     compilation_results[result_key] = current_result
    #     compilation_results[result_key]['lvl'] = lvl
    #     compilation_results[result_key]['part'] = part
    #     compilation_results[result_key]['name'] = result_key

    update_compilation_results(config, compilation_results)
    # input(' ok ')
    produce_latex(config)
    fill_obsidian(config, compilation_results)

def produce_latex(config):
    if not os.path.exists(config['report_path']):
        os.makedirs(config['report_path'])
    contents = json.load(open(config['results_path']))['results']
    latex_content = []

    def traverse_structure(structure, level):
        if isinstance(structure, dict):
            for key, value in structure.items():
                if level == 0:
                    latex_content.append(f"\\section{{{key}}}")
                elif level == 1:
                    latex_content.append(f"\\subsection{{{key}}}")
                elif level == 2:
                    latex_content.append(f"\\subsubsection{{{key}}}")
                else:
                    latex_content.append(f"\\paragraph{{{key}}}")
                
                traverse_structure(value, level + 1)
        elif isinstance(structure, list):
            for item in structure:
                traverse_structure(item, level)
        elif isinstance(structure, str):
            latex_content.append(structure)

    traverse_structure(contents, 0)
    with open(os.path.join(config['report_path'], 'report.tex'), 'w') as f:
        f.write("\n\n".join(latex_content))


def update_compilation_results(config, compilation_results):
    # Initialize the results file if it doesn't exist
    if not os.path.exists(os.path.dirname(config['results_path'])):
        os.makedirs(os.path.dirname(config['results_path']))
        with open(config['results_path'], 'w') as f:
            json.dump({"structure": config['report_structure'], "results": config['report_structure']}, f, indent=4)
    
    # Load existing results
    with open(config['results_path'], 'r') as f:
        existing_results = json.load(f)
    
    def find_node(structure, lvl, part, current_lvl=0, current_part=0, path=[]):
        if current_lvl == lvl and current_part == part:
            return path
        
        if isinstance(structure, dict):
            for key, value in structure.items():
                result = find_node(value, lvl, part, current_lvl + 1, current_part, path + [key])
                if result:
                    return result
        elif isinstance(structure, list):
            for index, item in enumerate(structure):
                result = find_node(item, lvl, part, current_lvl, index, path + [index])
                if result:
                    return result
        return None

    # Update the results
    for k, result in compilation_results.items():
        lvl = result['lvl']
        part = result['part']
        name = result['name']
        
        print('\n\nLooking for node with lvl {} and part {} - Name {}'.format(lvl, part, name))
        # Find the corresponding node in the structure
        hierarchy = find_node(config['report_structure'], lvl, part, current_lvl=0, current_part=0)
        
        if hierarchy:
            # Navigate to the correct place in the results
            current_level = existing_results['results']
            for h in hierarchy[:-1]:
                current_level = current_level[h]
            
            if isinstance(current_level, dict):
                if isinstance(current_level[hierarchy[-1]], list):
                    current_level[hierarchy[-1]][part] = {name: result['result']}
                elif isinstance(current_level[hierarchy[-1]], str):
                    current_level[hierarchy[-1]] = {name: result['result']}
            elif isinstance(current_level, list):
                current_level[part] = {name: result['result']}
    
    # Save the updated results
    with open(config['results_path'], 'w') as f:
        json.dump(existing_results, f, indent=4)


    
def fill_obsidian(config, compilation_results):

    focus_node_path = os.path.join(config['interactive_graph_path'], config['focus_node'] + ".md")
    # FORMATTING 
    if not is_leaf(focus_node_path): 
        compiled_text = []
        current_lvl = compilation_results[list(compilation_results.keys())[0]]['lvl']
        for k in compilation_results.keys(): 

            # TAKING INTO ACCOUNT SECTION CHANGES WHEN COMPILING
            if compilation_results[k]['lvl'] > current_lvl: 
                # get the new section: its lvl-th sub_titles from the section structure
                new_section = get_section_structure(focus_node_path)['subs_titles'][current_lvl]
                compiled_text.append(fill_section_template({"name": new_section, "lvl": current_lvl}, only_section = True))
                current_lvl = compilation_results[k]['lvl']

            compiled_text.append(fill_section_template(compilation_results[k]))
        mome.update_section(focus_node_path, "Results", "\n\n".join(compiled_text))
        # mome.update_section(focus_node_path, "Results", "\n\n".join([compilation_results[k]['result'] for k in compilation_results.keys()]))
    momeutils.crline('Compilation results: \n{}'.format(json.dumps([compilation_results[k]['compiled'] for k in compilation_results.keys()], indent = 4)))

def fill_section_template(current_result, only_section = False):
    # ASSUMING .section_template.txt exists in the folder 
    
    template = open(os.path.join(os.path.dirname(__file__), '.section_template.txt'), 'r').read()
    section_type = "section" if current_result['lvl'] == 0 else "sub" * current_result['lvl'] + "section"
    if only_section:
        template = template.strip().split('\n')[0]
        template = template.replace('ZENAME', current_result['name']).replace('section_type', section_type)
        return template
    return template.replace('section_type', section_type).replace('ZENAME', current_result['name']).replace('ZEPART', str(current_result['part'])).replace('ZERESULT', current_result['result'])


def compile_node(c, target_section = "Control center"): 
    paragraph_controls = momeutils.parse_json(mome.get_node_section(c, target_section))
    if paragraph_controls['content'] is None: 
        return {'compiled': False, 'result': f'No content to compile for {c}'}
    
    paragraph_reprez = {k:v for (k, v) in paragraph_controls.items() if (k != "nb_paragraphs" and v is not None)}
    paragraph_reprez = json.dumps(paragraph_reprez, indent = 4)
    test = generate_paragraph_subcontents(paragraph_reprez, paragraph_controls['nb_paragraphs'])
    # test= ["hello", "my", "name"]
    s = "\n\n* Paragraph ".join([''] + [str(i) + f": {t}" for i, t in enumerate(test)])
    p ="As an expert AI writer, you are provided with a high-level view of some paragraph contents. Based on the information, generate the text for each paragraph: {}".format(s)
    result = paragraph_writer2(test)
    # result = momeutils.basic_task(p)
    # result = paragraph_writer_enhanced(json.dumps(paragraph_controls, indent = 4))

    mome.update_section(c, "Results", result)
    return {'compiled': True, 'result': result}

def get_focus_node(config, targets = ['Section structure', 'Control center']): 

    focus_node_path = os.path.join(config['interactive_graph_path'], config['focus_node'] + ".md")
    result = {"path": focus_node_path}
    for t in targets:
        if mome.check_section(focus_node_path, t): 
            result[t.lower().replace('section', '').replace('center', '').strip()] = momeutils.parse_json(mome.get_node_section(focus_node_path, t))
    
    return result

def tmp_key_formatting(s, up_ = False):
    result = []
    for char in s:
        if char.isupper():
            if result:  # Avoid adding a space at the beginning
                result.append(' ')
            if up_:
                result.append(char)
            else: 
                result.append(char.lower())
        else:
            result.append(char)
    return ''.join(result)


def find_next_level_structure(report_structure, hierarchy):

    next_level_structure = report_structure

    for level in hierarchy[1:]: 
        # print(level, tmp_key_formatting(level))
        if isinstance(next_level_structure, dict):
            for k in next_level_structure.keys():
                if k.lower() == tmp_key_formatting(level):
                    next_level_structure = next_level_structure[k]
                    # print('Found {}'.format(k))
                    # print('Structure:\n{}'.format(next_level_structure))
                    break
        elif isinstance(next_level_structure, list):
            for i, v in enumerate(next_level_structure):
                str_v = v if isinstance(v, str) else list(v.keys())[0]
                if str_v.lower() == tmp_key_formatting(level):
                    next_level_structure = next_level_structure[i]
                    # print('Found {}'.format(str_v))
                    # print('Structure:\n{}'.format(next_level_structure))
                    break                   
    

    children = []
    if isinstance(next_level_structure, dict):
        next_level_structure = list(next_level_structure.values())[0]
    for c in next_level_structure: 
        if isinstance(c, dict): 
            children.append(list(c.keys())[0])
        elif isinstance(c, str): 
            children.append(c)
        else: 
            raise TypeError('Unrecognized type {} for next level structure {}'.format(type(c), c))  
    return children

def subs_titles_syntax_check(focus_node_contents):
    """
    Currently, only ensures that the subs_titles are in title case
    """
    focus_node_contents['structure']['subs_titles'] = [s.title() for s in focus_node_contents['structure']['subs_titles']]
    mome.update_section(focus_node_contents['path'], 'Section structure', momeutils.j_deco(focus_node_contents['structure']))


def structure_propagation(config_path = None, **kwargs): 
    config= load_config(config_path, **kwargs)
    focus_node = get_focus_node(config)
    hierarchy = collect_hierarchy_to_focus_node(config)

    
    subs_titles_syntax_check(focus_node)  

    # collect the initial contents (first level) from the report structure 
    next_level_structure = find_next_level_structure(config['report_structure'], hierarchy)

    if next_level_structure != focus_node['structure']['subs_titles']: # if the user has updated something 
         
        # Based on the focus_node['structure']['subs_titles'], figure out how the downstream names must change for the already existing nodes (all existing nodes after those potentially added by the user will undergo a name change)
        to_change = [] 
        to_add= []
        for i in range(len(focus_node['structure']['subs_titles'])):
            if focus_node['structure']['subs_titles'][i] in next_level_structure:
                if next_level_structure.index(focus_node['structure']['subs_titles'][i]) != i:
                    to_change.append({'node' : focus_node['structure']['subs_titles'][i],
                                      'initial_index': next_level_structure.index(focus_node['structure']['subs_titles'][i]), 
                                      'current_index': i}) 
            else: 
                to_add.append({'node': focus_node['structure']['subs_titles'][i], 
                               'current_index': i})
        to_remove = [{"node": n, "current_index" : i} for i, n in enumerate(next_level_structure) if n not in focus_node['structure']['subs_titles']]        

        current_dynasty = format_dynasty((mome.collect_dynasty_paths(focus_node['path'], include_root=True, preserve_hierarchy=True)), keep_path= True)

        # momeutils.dj({'to_change': to_change, 
        #               'to_add': to_add, 
        #               "to_remove": to_remove})
        
        current_control_center = focus_node['control']

        

        # UPDATE EXISTING NODES  
        for node in to_change: 

            current_node_path = collect_path_from_formatted_dynasty(node['node'], current_dynasty['children'])
            lvl, part, name, hash = split_node_for_info(current_node_path)
            new_name = f"lvl{lvl}_part{node['current_index']}_{name}_{hash}"
            # ideally, we should also change children names but that would imply first changing leaves and then bringing information back up to ensure links stay valid
            # mome.obsidian_rename_node(current_node_path, new_name)   
            hierarchical_rename(current_node_path, new_name)         

            current_dynasty['children'][node['initial_index']]['path'] = os.path.join(os.path.dirname(current_node_path), f"{new_name}.md")
            
            # update links in the focus node 
            mome.replace_link(focus_node['path'], momeutils.bn(current_node_path), new_name)

        # Prepare missing nodes creation --> nodes should be added in 'pour' so that changes in the template can be handled 
        for node in to_add:
            current_contents = get_default_section_dict()
            # current_control_center= get_control_center(focus_node['path'])
            current_control_center = momeutils.insert_key_at_idx(current_control_center, 
                                                                 node['current_index'], 
                                                                 node['node'], 
                                                                 _value= current_contents)
            
            add_lvl = 1 + int(os.path.basename(focus_node['path']).split('_')[0].replace('lvl',''))
            current_hash = mome.get_short_hash(os.path.basename(focus_node['path']).split('.')[0], 15)
            current_node_name = f"lvl{add_lvl}_part{node['current_index']}_{node['node'].title().replace(' ', '')}_{current_hash}.md"
            current_dynasty['children'].insert(node['current_index'], 
                                               {'path': os.path.join(os.path.dirname(focus_node['path']), current_node_name), 
                                                'children': []})
            
            mome.update_section(focus_node['path'], 'Control center', momeutils.j_deco(current_control_center))

            # Updating links --> Adding the link too early introduces problems when parsing the hierarchy
            # mome.add_link_at_position(focus_node['path'], current_node_name , node['current_index'])

        # momeutils.dj(to_remove)
        # momeutils.dj(current_dynasty['children'])
        # Remove nodes
        for node in to_remove:
            # print(node['node'], list(current_control_center.keys()), node['node'] in list(current_control_center.keys()))
            node_path = collect_path_from_formatted_dynasty(node['node'], current_dynasty['children'])

            clean_dynasty(node_path, include_root=True)
            # also, to remove from control center 
            # current_control_center= focus_node['control']
            current_control_center.pop(node['node'])

            mome.update_section(focus_node['path'], 'Control center', momeutils.j_deco(current_control_center))
            # current_dynasty['children'].pop(node['current_index'])

            # Actually removing from the dynasty requires some gymnastics because the initial indices may be affected by previous operations
            node_to_remove = [n for n in current_dynasty['children'] if n['path'] == node_path][0]
            current_dynasty['children'].remove(node_to_remove)

            # And finally, pop from links 
            mome.remove_links(focus_node['path'], [momeutils.bn(node_path)]) 

        current_dynasty_copy = copy.deepcopy(current_dynasty)

        # SAVING THE FINAL REPORT STRUCTURE 
        config['report_structure'] = update_report_structure(config, current_dynasty_copy, focus_node['path'])
        # momeutils.dj(config['report_structure'])
        # report_structure= config['report_structure']
        # momeutils.dj(current_dynasty)
        # current_dynasty_dict = dynasty_to_report_structure(current_dynasty)
        # momeutils.dj(current_dynasty_dict)
        # formatted_hierarchy = [tmp_key_formatting(h).title() for h in hierarchy[1:]]
        # # momeutils.dj(formatted_hierarchy)
        # momeutils.update_nested_dict(report_structure, formatted_hierarchy, current_dynasty_dict)
        # # momeutils.dj(report_structure)
        # # input('o k ? ')
        # config['report_structure'] = report_structure
        save_config(config, config_path)

def hierarchical_rename(current_node_path, new_name):
    # Collect the current dynasty paths
    current_dynasty = format_dynasty(
        mome.collect_dynasty_paths(current_node_path, include_root=True, preserve_hierarchy=True),
        keep_path=True
    )

    momeutils.crline('Working on {}'.format(current_node_path))    
    new_hash = mome.get_short_hash(new_name, 15)

    # Update the current node
    update_node_and_links(current_node_path, new_name, new_hash)
    momeutils.uinput('Updated')
    # Recursively update children
    for child in current_dynasty['children']:
        child_path = child['path']
        lvl, part, name, hash = split_node_for_info(child_path)
        new_child_name = f"lvl{lvl}_part{part}_{name}_{new_hash}"
        hierarchical_rename(child_path, new_child_name)

def update_node_and_links(node_path, new_name, new_hash):
    # Get current links
    current_links = mome.get_node_links(node_path)
    new_links_names = []

    for link in current_links:
        lvl, part, name, hash = split_node_for_info(link)
        new_links_names.append(f"lvl{lvl}_part{part}_{name}_{new_hash}")

    print('New links: {}'.format(new_links_names))
    # Update links and rename node
    mome.update_link_section(node_path, new_links_names)
    mome.obsidian_rename_node(node_path, new_name)


# def hierarchical_rename(current_node_path, new_name):

#     # Collect the current dynasty paths
#     current_dynasty = format_dynasty(
#         mome.collect_dynasty_paths(current_node_path, include_root=True, preserve_hierarchy=True),
#         keep_path=True
#     )
#     print(json.dumps(current_dynasty, indent = 4))
#     print(new_name, mome.get_short_hash(new_name, 15)) # this is the new name
#     new_hash = mome.get_short_hash(new_name, 15)

#     # =======================================
#     # EXAMPLE FOR THE CURRENT NODE, THIS HAS TO BE DONE RECURSIVELY
#     current_links = mome.get_node_links(current_node_path)
#     new_links_names = []
#     for link in current_links:
#         lvl, part, name, hash = split_node_for_info(link)
#         new_links_names.append(f"lvl{lvl}_part{part}_{name}_{new_hash}")

#     # renaming 
#     mome.update_link_section(current_node_path, new_links_names)
#     mome.obsidian_rename_node(current_node_path, os.path.join(os.path.dirname(current_node_path), new_name + ".md"))
        


def update_report_structure(config, current_dynasty, focus_node_path):
    report_structure = config['report_structure']
   
    current_dynasty_dict = dynasty_to_report_structure(current_dynasty)
    formatted_hierarchy = [tmp_key_formatting(h).title().replace('  ', ' ') for h in collect_hierarchy_to_focus_node(config)[1:]]

    momeutils.update_nested_dict(report_structure, formatted_hierarchy, current_dynasty_dict)
    return report_structure
        
def dynasty_to_report_structure(current_dynasty):
    report_structure = []

    for node in current_dynasty['children']:
        node_name = tmp_key_formatting(split_node_for_info(node['path'])[-2]).title()
        
        if node['children']:
            # If the node has children, recursively convert them
            child_structure = dynasty_to_report_structure(node)
            report_structure.append({node_name: child_structure})
        else:
            # If the node has no children, it's a leaf node
            report_structure.append(node_name)

    return report_structure


def collect_path_from_formatted_dynasty(node_name, current_dynasty): 
    # print(json.dumps(current_dynasty, indent=4))
    # momeutils.uinput("{}".format(json.dumps(current_dynasty, indent =4)))
    for nn in current_dynasty: 
        # momeutils.crline(nn['name'])
        if 'name' in nn.keys():
            if nn['name'].lower().strip() == node_name.lower().strip(): 
                return nn['path']
        
def split_node_for_info(path):

    # p = os.path.basename(path).split('.')[0]
    p = momeutils.bn(path)
    if '_' in p: 
        c = p.split('_')
        lvl = int(c[0].replace('lvl', ''))
        part = int(c[1].replace('part', ''))
        name = c[2]
        hash = c[3]
        return lvl, part, name, hash 
    else: 
        return 0,0,"",p
    


def node_expansion_colab(config_path = None, **kwargs): 
    config = load_config(config_path, **kwargs)
    focus_node_path = os.path.join(config['interactive_graph_path'], config['focus_node'] + ".md")
    
    parent_hash = mome.get_short_hash(focus_node_path, 15)
    # GETS THE JSON WITH EACH PART (CAN BE SECTION OR SUBSECTION)
    focus_node_contents = momeutils.parse_json(mome.get_node_section(focus_node_path)) # Collects the first section
    focus_node_control = momeutils.parse_json(mome.get_node_section(focus_node_path, "Control center")) 
    
    # check if keys are the same 
    assert list(focus_node_contents.keys()) == list(focus_node_control.keys())

    result_node = mome.add_node_to_graph(config['interactive_graph_path'],
                                        contents = {"Results": ""}, 
                                        tags = ['result_node'],
                                        parent_path = focus_node_path, 
                                        name_override = "results_" + parent_hash,
                                        use_hash = False)
    
    current_tag = mome.get_file_tags(focus_node_path)[0] # CAREFUL FOR THE 0, IN CASE THERE ARE MULTIPLE TAGS AT SOME POINT 
    section_level = len(current_tag.split('_')) + 1
    added_nodes = []
    for i, k in enumerate(focus_node_contents.keys()): 
        # NAME CONVENTION IS: lvlI_partJ_name_parenthash
        n = add_subnode_from_contents_control(config, focus_node_path, focus_node_contents[k], focus_node_control[k], k, current_tag, section_level, i, parent_hash)
        added_nodes.append(n)
    
    config['last_nodes_added'] = added_nodes
    
    # enhance_root_structure(config)
    save_config(config, config_path)
    return config

def update_existing_structure(structure, **kwargs): 
    for k, v in kwargs.items(): 
        if k in structure.keys(): 
            structure[k] = v
    return structure

def initiate_control_center(**kwargs): 
    c = {
        "hierarchy_location": None, 
        "high_level_context": None, 
        "things_said_before": None, 
        "content": None,
        "where_this_is_going": None,
        "nb_paragraphs": 3,
        "examples": None, 
        "specific_viewpoint": None, 
        "references": None,
        "visuals": None 
    }

    for k, v in kwargs.items():
        if k in c.keys(): 
            c[k] = v
    return c 


def tmp_get_section_org(section_content):   
    sentences = section_content.split('.')

    ks = {" ".join(s.split()[-2:]).strip().replace(' ', '_'): s for s in sentences if len(s) > 0}
    return ks 


def add_subnode_from_contents_control(config, focus_node_path, contents, control, subname, current_tag, section_level, paragraph_id, parent_hash): 
    
    if control['template'].strip().lower() == "direct": # means that this is going to be directly used to write 
            tag = ['to_compile']
            focus_contents = momeutils.parse_json(mome.get_node_section(focus_node_path)) # Collects the first section
            t = initiate_control_center(content = contents, 
                                    things_said_before = "\n".join([focus_contents[kk] for kk in list(focus_contents.keys())[:list(focus_contents.keys()).index(subname)]]),
                                    where_this_is_going = "\n".join([kk for kk in list(focus_contents.keys())[list(focus_contents.keys()).index(subname)+1:]]),
                                    )
            node_contents = {"Structure": momeutils.j_deco(t), "Results" : ""}
    else: 
        section_org = tmp_get_section_org(contents)
        node_contents = {"Base contents": momeutils.j_deco(section_org), # AI RESULTS 
                            "Control center": momeutils.j_deco(setup_control_params(section_org)), 
                        "Section structure": momeutils.j_deco(setup_section_structure(section_org)),
                        }
        
        tag = ['sub_' + current_tag]

    new_part = mome.add_node_to_graph(config['interactive_graph_path'],
                                    contents = node_contents,
                                    tags = tag,
                                    parent_path = focus_node_path, 
                                    # node_prefix = k, 
                                    name_override = "lvl{}_part{}_{}_{}".format(section_level, paragraph_id, 
                                                                                re.sub(r'[^a-zA-Z0-9\s]', '', subname).strip().lower().replace(' ', '_'),
                                                                                parent_hash ),
                                    use_hash = False)
    return new_part

def do_section_struct_to_base_contents(focus_node_path): 
    structure_contents = momeutils.parse_json(mome.get_node_section(focus_node_path, "Section structure"))
    
    # TMP MANUAL FOR NOW !!! 
    computed_contents = {"_".join(s.strip().replace(',', '').split()[:2]).lower(): s for s in structure_contents['initial_contents'].split('.') if len(s.strip()) > 2}
    # ABOVE SHOULD BE A LLM CALL  

    # REMOVE NODE DYNASTY (CLEANING)
    clean_dynasty(focus_node_path, include_root = False)
    # dynasty = mome.collect_dynasty_paths(focus_node_path, include_root = False, preserve_hierarchy = False)
    

    mome.update_section(focus_node_path, "Base contents", momeutils.j_deco(computed_contents))
    # save_config(config, config_path)

    # HANDLES CONTROL CENTER 
    do_control_center_from_base_contents(focus_node_path)
    # control_center_from_base_contents(config_path)

def do_control_center_from_base_contents(focus_node_path):
    base_contents = momeutils.parse_json(mome.get_node_section(focus_node_path))    
    control_center = {k: get_default_section_dict() for k in base_contents.keys()}
    mome.update_section(focus_node_path, "Control center", momeutils.j_deco(control_center))

def get_default_section_dict(): 
    return {"user_instruction" : None, 
        "additional_details": None, 
        "template": "default"}

def clean_dynasty(root, include_root, link_section = "Links"):
    """
    Removes children and cleans also the link sections, assuming include_root is false (otherwise, it is deleted) 
    """
    if root is None:
        momeutils.crline('Root node is None')
        return
    if not os.path.exists(root):
        momeutils.crline('Missing root node {}'.format(root))
        return
    dynasty = mome.collect_dynasty_paths(root, include_root = include_root, preserve_hierarchy = False)
    for node in dynasty: 
        os.remove(node)
    if not include_root: 
        mome.update_link_section(root, "", link_section = link_section)

def setup_control_center_from_hls(structure):
    subs_titles = gf_all(structure, show_structure=True)
    return setup_control_center(subs_titles)
 
def setup_control_center(named_templates): 

    base_format = {"user_instruction": None,
                   "additional_details": None,
                   "template": "default"}
    results = {}
    for i in range(len(named_templates)): 
        b = base_format.copy()
        if named_templates[i][1].strip() == "paragraph" or named_templates[i][1].strip() == "direct": 
            b['template'] = "direct"
        results[named_templates[i][0]] = b
    return results 

def setup_section_structure_from_hls(current_structure): 

    subs_titles = gf_all(current_structure, show_structure=True)
    initial_contents = ". ".join(["There is a {} about {}".format(s[1], s[0]) for s in subs_titles])
    return setup_section_structure(initial_contents = initial_contents, 
                                   subs_titles = [s[0] for s in subs_titles])

def setup_section_structure(**kwargs): 
    c = {"initial_contents": "", 
         "subs_titles": []}
    for k in kwargs.keys(): 
        if k in c.keys(): 
            c[k] = kwargs[k]
    return c

def setup_section_structure2(initial_contents): 
    contents_to_insert = ''
    if isinstance(initial_contents, dict): 
        contents_to_insert = "  ".join("{}: {}".format(k, v) for k,v in initial_contents.items())
    elif isinstance(initial_contents, list): 
        contents_to_insert = " ".join(initial_contents)
    else: 
        contents_to_insert = initial_contents
    return {"initial_contents": contents_to_insert, 
            "subs_titles" : [],
            "nb_subs": 2,}

def setup_control_params(suggested_sections): 
    if isinstance(suggested_sections, list): 
        parts = list(suggested_sections)
    elif isinstance(suggested_sections, dict): 
        parts = list(suggested_sections.keys())
    else: 
        raise TypeError('Unrecognized type in setup control params for :{}'.format(type(suggested_sections)))
    
    return {part: get_default_section_dict() for part in parts}




if __name__ == "__main__": 

    config_path = os.path.join(os.path.dirname(__file__), "config_{}.json".format(os.path.basename(__file__).split('.')[0]))
    # a file containing debugging contents
    rationale_path = os.path.join(os.path.dirname(__file__), "contents_ainimals.json")
    rationales = json.load(open(rationale_path))
    make_graph(config_path)
    # updating root
    
    config = json.load(open(config_path))

    section_structure = get_section_structure(os.path.join(os.path.dirname(__file__), "sir_interactive_graph", config['current_hash'] + ".md"))
    section_structure = update_existing_structure(section_structure, initial_contents = rationales['rationale'])
    
    # UPDATING ROOT 
    mome.update_section(os.path.join(os.path.dirname(__file__), "sir_interactive_graph", config['current_hash'] + ".md"), "Section structure", momeutils.j_deco(section_structure)) 

    # UPDATING OPERATION TOPIC 
    section_structure = get_section_structure(os.path.join(os.path.dirname(__file__), "sir_interactive_graph", "lvl0_part0_OperationTopic_2cf24dba5fb0a30" + ".md"))
    # section_structure = update_existing_structure(section_structure, initial_contents = rationales['rationale'])
    section_structure = update_existing_structure(section_structure, initial_contents = rationales['rationale'], subs_titles = rationales['different_subs_titles_in_operationtopic'])
    mome.update_section(os.path.join(os.path.dirname(__file__), "sir_interactive_graph", "lvl0_part0_OperationTopic_2cf24dba5fb0a30" + ".md"), "Section structure", momeutils.j_deco(section_structure)) 

