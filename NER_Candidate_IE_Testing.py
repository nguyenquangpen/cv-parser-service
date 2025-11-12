import spacy
# from NER_Dataset_JsonToSpacyFormat import JsonToSpacyFormat
if __name__ == '__main__':

    trained_model = spacy.load('NER_Candidate_IE_model')
    # trained_model = spacy.load('NER_HardSoftSkill_Extract_model')
    print(trained_model.get_pipe("ner"))
    print(trained_model.get_pipe("ner").labels)
    # path = 'uploads/resumes/Akshay_Srimatrix.pdf'
    # json_path = "Dataset/Entity Recognition in Resumes.json"
    # converter = JsonToSpacyFormat(json_path)
    # data = converter.get_training_data()
    # pattern1 = data[1]
    # # print(pattern1[0])
    # text = pattern1[0]
    # # print(pattern1)

    with open ("Resume.csv", "r") as f:
        text = f.read()

    doc = trained_model(text)
    print(f"Text: {text}")
    print("Predicted Entities:")
    print("Entities:", [(ent.text, ent.label_) for ent in doc.ents])
    print("True Entities:")
    # print(pattern1[1])

'''
Predicted Entities:
Entities: [('IIIT Committee', 'hard_skills'), ('excellence', 'soft_skills'), ('IIIT Committee', 'hard_skills'), ('PERSONALLITY', 'hard_skills'), ('HTML', 'hard_skills'), ('Linux', 'hard_skills'), ('MICROSOFT ACCESS', 'hard_skills'), ('C, C++', 'hard_skills'), ('Java', 'hard_skills'), ('php', 'hard_skills'), ('Linux', 'hard_skills'), ('MS Access', 'hard_skills'), ('SQL', 'hard_skills'), ('MySql', 'hard_skills')]

True Entities:
{'entities': [(1155, 1199, 'Email Address'), (743, 1141, 'Skills'), (729, 733, 'Graduation Year'), (675, 702, 'College Name'), (631, 673, 'Degree'), (625, 629, 'Graduation Year'), (614, 623, 'College Name'), (606, 612, 'Degree'), (104, 148, 'Email Address'), (62, 68, 'Location'), (0, 14, 'Name')]}
'''