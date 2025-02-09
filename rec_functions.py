import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def _get_intersection_scores(student_interests, org_info): 

    pcts = []
    student_interests = set(student_interests)

    for org in org_info: 

        org_categories = set(org["Categories"])
        common = student_interests.intersection(org_categories)
        pcts.append(len(common) / len(student_interests))

    return pcts

def _get_cosine_sims(student_interests, org_info):

    org_descriptions = [org["Description"] for org in org_info]
    student_interest_text = " ".join(student_interests)
    documents = [student_interest_text] + org_descriptions

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])

    return cosine_similarities

def _get_composite_score(intersection_scores, cosine_scores):

    intersection_weight = 0.8
    cosine_weight = 0.2

    return (np.asarray(intersection_weight) * intersection_scores) + (np.asarray(cosine_weight) * cosine_scores)

def return_ranks(student_interests, org_info): 

    intersection_scores = _get_intersection_scores(student_interests, org_info)
    cosine_scores = _get_cosine_sims(student_interests, org_info)

    composite_scores = _get_composite_score(intersection_scores, cosine_scores)

    org_names = [org["Name"] for org in org_info]
    print(org_names)
    scores_dict = dict(zip(org_names, composite_scores[0]))
    print(scores_dict)

    return sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)