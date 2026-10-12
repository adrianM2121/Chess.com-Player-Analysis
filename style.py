import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

def zscores(baseline, player):
    """How many standard deviations the player is from the baseline, per feature."""
    mu, sd = baseline.mean(), baseline.std()
    return ((pd.Series(player) - mu) / sd).dropna()

def standardize(df):
    filled = df.fillna(df.mean())
    return (filled - filled.mean()) / filled.std()

def cosine_similarity(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def most_similar(Z, username, k=5):
    target = Z.loc[username].values
    sims = {u: cosine_similarity(target, Z.loc[u].values) for u in Z.index if u != username}
    return pd.Series(sims).sort_values(ascending=False).head(k)

def pca_by_hand(Z):
    """PCA from scratch: eigenvectors of the covariance matrix."""
    X = Z.values
    C = np.cov(X, rowvar=False)                 # feature-by-feature covariance
    eigvals, eigvecs = np.linalg.eigh(C)        # eigh: for symmetric matrices
    order = np.argsort(eigvals)[::-1]           # largest variance first
    eigvals, eigvecs = eigvals[order], eigvecs[:, order]
    coords = X @ eigvecs[:, :2]                 # project onto the top 2 directions
    explained = eigvals / eigvals.sum()
    return coords, eigvecs, explained

def pca_sklearn(Z, n=2):
    pca = PCA(n_components=n)
    coords = pca.fit_transform(Z.values)
    loadings = pd.DataFrame(pca.components_.T, index=Z.columns,
                            columns=[f"PC{i+1}" for i in range(n)])
    return coords, loadings, pca.explained_variance_ratio_

def cluster_styles(Z, k=4, seed=0):
    km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(Z.values)
    centers = pd.DataFrame(km.cluster_centers_, columns=Z.columns)
    return pd.Series(km.labels_, index=Z.index, name="cluster"), centers, km.inertia_