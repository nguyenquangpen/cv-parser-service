import spacy
import PyPDF2
from NER_Dataset_JsonToSpacyFormat import JsonToSpacyFormat
import NER_HardSoftSkill_Data
if __name__ == '__main__':

    trained_skill_model = spacy.load('NER_HardSoftSkill_Extract_model')
    print(trained_skill_model.pipe_names)
    print(trained_skill_model.get_pipe("ner").labels)
    data = NER_HardSoftSkill_Data.train
    index = 0
    doc = data[index]

    text = doc[0]
    labels = doc[1]
    results = trained_skill_model(text)


    print(text)
    # result = trained_skill_model(text)
    print("Result: ", results.ents)
    print("Predicted Skills:")
    print("Entities: ", [(ent.text, ent.label_) for ent in results.ents])
    print("True Skills:")
    print(labels)
'''
Predicted Entities:
Entities: [('IIIT Committee', 'hard_skills'), ('excellence', 'soft_skills'), ('IIIT Committee', 'hard_skills'), ('PERSONALLITY', 'hard_skills'), ('HTML', 'hard_skills'), ('Linux', 'hard_skills'), ('MICROSOFT ACCESS', 'hard_skills'), ('C, C++', 'hard_skills'), ('Java', 'hard_skills'), ('php', 'hard_skills'), ('Linux', 'hard_skills'), ('MS Access', 'hard_skills'), ('SQL', 'hard_skills'), ('MySql', 'hard_skills')]

True Entities:
{'entities': [(1155, 1199, 'Email Address'), (743, 1141, 'Skills'), (729, 733, 'Graduation Year'), (675, 702, 'College Name'), (631, 673, 'Degree'), (625, 629, 'Graduation Year'), (614, 623, 'College Name'), (606, 612, 'Degree'), (104, 148, 'Email Address'), (62, 68, 'Location'), (0, 14, 'Name')]}
'''