import sys

def levenshtein_distance(str1, str2):
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize the matrix
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # Populate the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                cost = 0
            else:
                cost = 1
            
            dp[i][j] = min(dp[i - 1][j] + 1,      # Deletion
                           dp[i][j - 1] + 1,      # Insertion
                           dp[i - 1][j - 1] + cost)  # Substitution
    
    
    for i in range(1, m + 1):
        print(dp[i])

    return dp[m][n]

# Example usage:
str1 = sys.argv[1]
str2 = sys.argv[2]
distance = levenshtein_distance(str1, str2)
print(f"Levenshtein distance between '{str1}' and '{str2}' is {distance}")