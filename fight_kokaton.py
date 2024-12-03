import os
import random
import sys
import math
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS=5 #爆弾個数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.dire=(+5,0)
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire=tuple(sum_mv) #向きを更新
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.centery= bird.rct.centery #こうかとん中心座標
        self.rct.left =bird.rct.right #こうかとんの右座標
        #こうかとんの向きに基づきビームの速度を設定
        self.vx, self.vy = bird.dire

        # ビーム画像の回転
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.img = pg.transform.rotozoom(self.img, angle, 1.0)
        
        # 初期配置の設定
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx // 5
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy // 5

 
    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)    


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    def __init__(self):
        self.fonto = pg.font.SysFont("hpg創英角ポップ体", 30)  # フォント設定
        self.color = (0, 0, 255)  # 青色
        self.score = 0  # スコア初期値
        self.img = self.fonto.render(f"score: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)  # 画面左下に配置

    def add_score(self, points: int):
        """
        スコアを加算する
        引数 points: 加算するポイント数
        """
        self.score += points

    def update(self, screen: pg.Surface):
        """
        現在のスコアを更新して画面に表示
        """
        self.img = self.fonto.render(f"score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)
    

class Explosion:
    """
    爆発エフェクトを表現するクラス
    """
    def __init__(self, center: tuple[int, int], life: int = 20):
        """
        引数:
            center: 爆発が発生する座標
            life: 爆発の持続時間（フレーム数）
        """
        self.images = [
            pg.transform.flip(pg.image.load("fig/explosion.gif"), False, False),
            pg.transform.flip(pg.image.load("fig/explosion.gif"), True, True),
        ]
        self.center = center
        self.life = life
        self.current_image = 0

    def update(self, screen: pg.Surface):
        """
        爆発エフェクトを更新し、画面に描画する。
        引数:
            screen: ゲーム画面のSurface
        """
        if self.life > 0:
            img = self.images[self.current_image]
            rct = img.get_rect(center=self.center)
            screen.blit(img, rct)
            self.life -= 1
            self.current_image = (self.current_image + 1) % len(self.images)




    



def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200)) #birdインスタンスを生成
    bomb = Bomb((255, 0, 0), 10) #Bombインスタンスを生成
    score=Score() #Scoreインスタンスを生成
    beam = None #beamインスタンス生成
    beams=[] #複数ビームを扱うリスト
    explosions=[] #爆発エフェクトリスト
    bombs=[ Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)
                beams.append(beam) #リスト追加            
        screen.blit(bg_img, [0, 0])
        
        #爆弾とこうかとんの衝突判定
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
            # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                fonto=pg.font.Font(None,80)
                txt=fonto.render("Gameover",True,(255,0,0))
                screen.blit(txt,[WIDTH//2-150,HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
        # こうかとんと爆弾の判定部分
        for beam in beams:
            for i, bomb in enumerate(bombs):
                if bomb is not None and beam.rct.colliderect(bomb.rct):
                    beams.remove(beam)  # 衝突したビームを削除
                    explosions.append(Explosion(bomb.rct.center))  # 爆発エフェクトを追加
                    bombs[i] = None  # 衝突した爆弾を削除
                    bird.change_img(6, screen)  # こうかとん画像変更
                    score.add_score(1)  # スコア更新
                    break

        #ビームの更新
        beams = [beam for beam in beams if check_bound(beam.rct) == (True, True)]
        for beam in beams:
            beam.update(screen)

        #爆弾の更新
        bombs = [bomb for bomb in bombs if bomb is not None]
        for bomb in bombs:
            bomb.update(screen)

        #爆発の更新
        explosions = [exp for exp in explosions if exp.life > 0]  # 爆発リストを更新
        for explosion in explosions:
            explosion.update(screen)

        #スコア更新
        score.update(screen)

        #こうかんとんの更新
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


 

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()

