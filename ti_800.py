import mome 
import momeutils 
import os 
import inspect 
import json 
import shutil 
import glob 
import re 

def paragraph_writer(paragraph_template = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    
    messages = [
            {"role": "system", "content": """
    You are a writing assistant with expertise in producing well-structured and coherent paragraphs. You are expected to generate a paragraph based on a provided template and a set of critical elements. 
    Answer in a JSON format as follows:
    ```json
    {{
    
        "result" : "The generated paragraph based on the provided template and critical elements."
    
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Paragraph Template\n{}\n\nUse the provided paragraph template to produce a well-structured and coherent paragraph under the key 'result'.\n\n".format(icl_examples, paragraph_template)}
    ]
    
    results = momeutils.parse_json(momeutils.ask_llm(messages, model = "g4o"))
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return results["result"]

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
        "last_nodes_added": []
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
            print(k, v)
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


def create_nodes_recursively(graph_folder, structure, parent_path=None, level=0, part=0, parent_hash=None):
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
                    create_nodes_recursively(graph_folder, item, created_node_path, level + 1, i, current_hash)
                else:
                    # Create leaf node

                    leaf_name = f"lvl{level + 1}_part{i}_{format_section_title(item)}_{current_hash}"

                    high_level_context = key # global view 
                    print(leaf_name, key)
                    things_said_before = section_population if len(section_population) >0 else None,
                    where_this_is_going = section_depopulation if len(section_depopulation) > 0 else None

                    leaf_contents = {
                        "Control center": momeutils.j_deco(make_theme_template(high_level_context = high_level_context,
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

    # Example structure
    structure = {
        "operation_topic": ['overview', {'issues_with_different_methods': [{"method_A": ["test0", "test1"]}, "method_B"]}],
        "technical_justification": ["related works and their limitation", "why we should go in the direction we chose"],
        "what_we_actually_did": ["overview", "technical details", {"results": ['experiment 0', {'experiment 1': ['background', 'setup', 'observations']}]}, "discussions"], 
            "conclusion": ["summary", "future work", "concluding remarks"]
    }

    # Root id
    base_hash = mome.get_short_hash("hello", 15)  # TMP

    # Create root node
    root_contents = {"root contents": "to_fill_root"}
    root_node_path = mome.add_node_to_graph(
        graph_folder=config['interactive_graph_path'],
        contents=root_contents,
        parent_path=None,
        tags=["root"],
        name_override=base_hash,
        use_hash=False
    )

    # Create nodes recursively
    create_nodes_recursively(config['interactive_graph_path'], structure, root_node_path, level=0, part=0, parent_hash=base_hash)

def is_leaf(current_node, target_tag = "results"): 
    tags= mome.get_file_tags(current_node)
    return target_tag in tags

def compile(config_path=None, **kwargs):
    config = load_config(config_path, **kwargs)
    focus_node_path = os.path.join(config['interactive_graph_path'], config['focus_node'] + ".md")
    if is_leaf(focus_node_path): 
        to_compile = [focus_node_path]
    else: 
        node_dynasty = mome.collect_dynasty_paths(focus_node_path, include_root=False, preserve_hierarchy=False)
        _, result_nodes = mome.collect_node_contents(config['interactive_graph_path'], tags = ['results'], return_paths = True)
        to_compile = [n for n in node_dynasty if n in result_nodes]
    print("\n* ".join([''] + [os.path.basename(n).split('.')[0] for n in to_compile]))
    for c in to_compile: 
        compile_node(c)

def compile_node(c, target_section = "Control center"): 
    paragraph_controls = momeutils.parse_json(mome.get_node_section(c, target_section))
    
    result = paragraph_writer(json.dumps(paragraph_controls, indent = 4))

    mome.update_section(c, "Results", result)

# def recursive_graph_maker(config_path, parent, current_structure):
    
#     config = load_config(config_path)
#     graph_folder = config['interactive_graph_path']
#     for k in current_structure.keys(): 
#         # print(k)
#         struct_below = current_structure[k]
#         node_contents = []
#         for i, s in enumerate(struct_below): 
#             if isinstance(s, str): 
#                 node_contents.append({"template" : 'direct',
#                                       "title" : s, 
#                                      "content": f"{s} is a paragraph"})
#             elif isinstance(s, dict): 

#                 sample_sub_keys = [f'{k} requires some reflexion']
#                 node_contents.append({"template": 'default',
#                                       "title" : s, 
#                                       "content": ", ".join(sample_sub_keys)})

#         section_node = mome.add_node_to_graph(graph_folder,
#                                                 contents = {"Base contents": "Needs contents compilation", #momeutils.j_deco({o:"\n* ".join([""] + out[o]) for o in out.keys()}),
#                                                             "Control center": "Needs control compilation", #momeutils.j_deco(control_params), 
#                                                             "Section structure": momeutils.j_deco(setup_section_structure(". ".join([n['content'] for n in node_contents]).capitalize())),  # that's the original + some controls (in case we wanna regen)
#                                                             "Results": ""},
#                                                 tags = ['section'],
#                                                 parent_path = parent, 
#                                                 node_prefix = re.sub(r'[^a-zA-Z0-9\s]', '', k).strip().lower().replace(' ', '_'), 
#                                                 use_hash = False)
#         print('Created section node {}'.format(section_node))
        
#         # confirming to propagate to base and control
#         do_section_struct_to_base_contents(section_node)

#         # here update control based on previously collected data 
#         section_controls = momeutils.parse_json(mome.get_node_section(section_node, "Control center"))
#         for i, (k, nc) in enumerate(zip(section_controls.keys(), node_contents)): 
#             section_controls[k]['template'] = nc['template']
#         mome.update_section(section_node, "Control center", momeutils.j_deco(section_controls))

#         # then, expand using node_expansion_colab
#         new_tmp_config = node_expansion_colab(config_path, focus_node = os.path.basename(section_node).split('.')[0])
#         for i in range(len(node_contents)): 
#             node_contents[i]['link'] = new_tmp_config['last_nodes_added'][i]
#             if node_contents[i]['template'] != "direct": 
#                 # input(struct_below)
#                 recursive_graph_maker(config_path, node_contents[i]['link'], struct_below[i])


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

def make_theme_template(**kwargs): 
    c = {
        "high_level_context": None, 
        "content": None,
        "things_said_before": None, 
        "where_this_is_going": None,
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
            t = make_theme_template(content = contents, 
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
        if named_templates[i][1] == "paragraph": 
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

    # make_graph(os.path.join(os.path.dirname(__file__), "config_ti.json"))
    compile(os.path.join(os.path.dirname(__file__), "config_ti.json"))