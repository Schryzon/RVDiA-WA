"""
A script file, similar to scripts.main from RVDiA
"""

def heading(direction:int):
        result =[]
        ranges = [
        [0, 45, "Utara"], [46, 90, "Timur Laut"],
        [91, 135, "Timur"], [136, 180, "Tenggara"],
        [181, 225, "Selatan"], [226, 270, "Barat Daya"],
        [271, 315, "Barat"], [316, 360, "Barat Laut"]
        ]

        for i in ranges:
            if direction in range(i[0], i[1] + 1):
                result.append(i[2])

        return result[0] 