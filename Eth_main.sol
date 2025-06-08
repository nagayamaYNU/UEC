// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

//登録情報を階層構造で管理する
contract HierarchyManager {
    // ノード構造体を定義
    struct Node {
        string name;                      // ノード名
        mapping(string => Node) children; // 子ノード（階層構造を管理）
        string[] childNames;              // 子ノード名のリスト（順序を保持）
        bool exists;                      // ノードの存在フラグ
    }

    Node private root; // ルートノードを定義

    // コンストラクタでルートノードを初期化
    constructor() {
        root.name = "root";
        root.exists = true;
    }

    // 指定したパスを階層構造に追加
    function addPath(string[] memory path) public {
        Node storage current = root; // ルートから開始

        for (uint256 i = 0; i < path.length; i++) {
            string memory key = path[i]; // 現在のパス要素を取得

            // ノードが存在しない場合、新規作成
            if (!current.children[key].exists) {
                current.children[key].name = key;  // ノード名を設定
                current.children[key].exists = true; // 存在フラグをtrueに
                current.childNames.push(key); // 子ノード名リストに追加
            }
            current = current.children[key]; // 次の階層へ
        }
    }

    // 複数のパスを一度に追加
    function addMultiplePaths(string[][] memory paths) public {
        for (uint256 i = 0; i < paths.length; i++) {
            addPath(paths[i]); // 各パスを順番に追加
        }
    }

    // 指定したノードのすべての子ノード名を取得
    function getChildren(string[] memory path) public view returns (string[] memory) {
        Node storage current = root; // ルートから開始

        // 指定されたパスを辿る
        for (uint256 i = 0; i < path.length; i++) {
            string memory key = path[i];
            require(current.children[key].exists, "Path does not exist"); // ノードが存在することを確認
            current = current.children[key]; // 次の階層へ
        }

        return current.childNames; // 子ノード名のリストを返す
    }

    // 指定したノードの子ノード数を取得
    function getChildCount(string[] memory path) public view returns (uint256) {
        Node storage current = root; // ルートから開始

        // 指定されたパスを辿る
        for (uint256 i = 0; i < path.length; i++) {
            string memory key = path[i];
            require(current.children[key].exists, "Path does not exist"); // ノードが存在することを確認
            current = current.children[key]; // 次の階層へ
        }

        return current.childNames.length; // 子ノード数を返す
    }

    // 指定したノードの子ノードをページネーション形式で取得
    function getChildrenPaginated(
        string[] memory path, // 対象ノードのパス
        uint256 start,        // 取得開始インデックス
        uint256 count         // 取得する個数
    ) public view returns (string[] memory) {
        Node storage current = root; // ルートから開始

        // 指定されたパスを辿る
        for (uint256 i = 0; i < path.length; i++) {
            string memory key = path[i];
            require(current.children[key].exists, "Path does not exist"); // ノードが存在することを確認
            current = current.children[key]; // 次の階層へ
        }

        require(start < current.childNames.length, "Start index out of range"); // インデックスの範囲をチェック

        uint256 end = start + count; // 終了インデックスを計算
        if (end > current.childNames.length) {
            end = current.childNames.length; // リストの終端を超えないように調整
        }

        uint256 resultLength = end - start; // 取得する配列のサイズを計算
        string[] memory result = new string[](resultLength); // 結果格納用の配列を作成

        // 指定範囲の子ノード名を格納
        for (uint256 i = 0; i < resultLength; i++) {
            result[i] = current.childNames[start + i];
        }

        return result; // 取得結果を返す
    }

    // 可変部分を持つパスを一括登録(この関数は使っていない、将来的な属性数増加のためにとりあえず書いた)
    function addPathsWithVariable(
        string[] memory basePath,    // ベースパス
        string[] memory variableParts // 可変部分
    ) public {
        for (uint256 i = 0; i < variableParts.length; i++) {
            string[] memory fullPath = new string[](basePath.length + 1); // フルパス用配列を作成

            // ベースパスをコピー
            for (uint256 j = 0; j < basePath.length; j++) {
                fullPath[j] = basePath[j];
            }

            // 可変部分を最後に追加
            fullPath[basePath.length] = variableParts[i];

            // 生成したフルパスを登録
            addPath(fullPath);
        }
    }
}
