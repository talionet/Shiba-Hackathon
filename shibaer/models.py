

from keras.layers import Input, Embedding, Flatten, concatenate, Lambda, Dense
from keras.regularizers import l2
from keras import backend as K
from keras.models import Model

from shibaer.util import load_pickle_files, read_metadata

EMBEDDING_REGULARIZATION = .0


def visit2vec(numeric_data_size, categocial_columns, categorical_families, targets):
    """
    Build a visit2vec model -- representation of a single visit

    :param numeric_data_size: int

    :param categocial_columns: list
        (name, n_cats, emb_size)

    :param categorical_families: list
        [{"name":"ICD-9", "n-items": 67, "emb-size":10, "n-cols":3}, ...

    :param targets: list
        (target_name, target_size)

    :return:
    """

    # All numeric data goes here
    numeric_data = Input(shape=(numeric_data_size,))

    # Embeddings for categorical columns
    simple_categorical_inputs = []
    simple_categoricals = []
    for col_name, n_items, emb_size in categocial_columns:
        print("Building col: ", col_name)

        this_input = Input(shape=(1,), name="input_" + col_name)
        this_emb = Embedding(n_items, emb_size, name="embedding_" + col_name, embeddings_regularizer=l2(EMBEDDING_REGULARIZATION))
        this_out = Flatten(name="flat_" + col_name)(this_emb(this_input))

        simple_categorical_inputs.append(this_input)
        simple_categoricals.append(this_out)

    # Embeddings for categorical families
    fam_categorical_inputs = []
    fam_categoricals = []
    for c_fam in categorical_families:
        print("Building family: ", c_fam["name"])
        this_emb = Embedding(c_fam["n-items"], c_fam["emb-size"], name="embedding_" + c_fam["name"], embeddings_regularizer=l2(EMBEDDING_REGULARIZATION))
        for i in range(c_fam["n-cols"]):
            this_input = Input(shape=(1,), name="input_" + c_fam["name"] + "_" + str(i))
            this_out = Lambda(lambda inp: K.mean(inp, axis=1))(this_emb(this_input))

            fam_categorical_inputs.append(this_input)
            fam_categoricals.append(this_out)

    user_vector = concatenate([numeric_data] + simple_categoricals + fam_categoricals, name="user_vector")

    outputs = []
    for target_name, target_size in targets:
        print("Building otuput: ", target_name)
        this_out = Dense(target_size, name="target_"+target_name)(user_vector)
        outputs.append(this_out)

    model = Model(inputs=[numeric_data]+simple_categorical_inputs+fam_categorical_inputs, outputs=outputs)
    model.summary()


def train(data):
    # Numeric data
    meta_data = read_metadata()
    numeric_cols = meta_data.loc[meta_data.data_type == 'numeric'].index
    numeric_data_size = numeric_cols.shape[0]

    categocial_columns = [
        ("gender", 2, 2),
    ]


    categorical_families = [

    ]

    targets = [("dead", 2)]

    model = visit2vec(numeric_data_size, categocial_columns, categorical_families, targets)


if __name__ == "__main__":
    cats = [("cat1", 20, 5), ("cat2", 20, 5)]

    cat_fam = [
        {"name":"ICD-9", "n-items": 200, "emb-size":10, "n-cols":3},
        {"name": "drugs", "n-items": 500, "emb-size": 10, "n-cols": 3}
    ]

    targets = [("is-dead", 2)]

    # visit2vec(numeric_data_size=10, categocial_columns=cats, categorical_families=cat_fam, targets=targets)

    data = load_pickle_files("DATAA", "ER", is_small=True)
    train(data)

